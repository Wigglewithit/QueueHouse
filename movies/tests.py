from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse

from .models import Movie, Review, WatchlistEntry


class MovieFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('alice', password='TestPassword-246!')
        cls.other = get_user_model().objects.create_user('bob', password='TestPassword-246!')
        cls.staff = get_user_model().objects.create_user('staff', password='TestPassword-246!', is_staff=True)
        cls.movie = Movie.objects.create(title='Example Film', year=2001, genre='Drama')

    def test_catalog_creation_requires_staff(self):
        url = reverse('add_movie')
        payload = {'title': 'New Film', 'year': 2000, 'genre': 'Drama'}
        self.assertEqual(self.client.post(url, payload).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(url, payload).status_code, 403)
        self.assertFalse(Movie.objects.filter(title='New Film').exists())
        self.client.force_login(self.staff)
        self.assertRedirects(self.client.post(url, payload), reverse('movie_list'))
        self.assertTrue(Movie.objects.filter(title='New Film').exists())

    def test_watchlist_is_private_and_mutations_require_post(self):
        own = WatchlistEntry.objects.create(user=self.user, movie=self.movie)
        foreign_movie = Movie.objects.create(title='Other users only')
        other = WatchlistEntry.objects.create(user=self.other, movie=foreign_movie)
        self.client.force_login(self.user)
        response = self.client.get(reverse('watchlist'))
        self.assertContains(response, self.movie.title)
        self.assertNotContains(response, foreign_movie.title)
        for name in ('toggle_watched', 'toggle_favorite', 'remove_from_watchlist'):
            self.assertEqual(self.client.get(reverse(name, args=[own.pk])).status_code, 405)
            self.assertEqual(self.client.post(reverse(name, args=[other.pk])).status_code, 404)
        other.refresh_from_db()
        self.assertFalse(other.watched)
        self.assertFalse(other.favorite)
        for name in ('toggle_watched', 'toggle_favorite'):
            self.assertEqual(self.client.post(reverse(name, args=[own.pk])).status_code, 302)
        own.refresh_from_db()
        self.assertTrue(own.watched)
        self.assertTrue(own.favorite)
        self.client.post(reverse('remove_from_watchlist', args=[own.pk]))
        self.assertFalse(WatchlistEntry.objects.filter(pk=own.pk).exists())

    def test_add_is_idempotent_and_shows_saved_state(self):
        self.client.force_login(self.user)
        url = reverse('add_to_watchlist', args=[self.movie.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(WatchlistEntry.objects.count(), 1)
        self.assertContains(self.client.get(reverse('movie_list')), 'In your watchlist')

    def test_csrf_is_enforced(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(reverse('add_to_watchlist', args=[self.movie.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(WatchlistEntry.objects.count(), 0)

    def test_search_pagination_and_filters(self):
        Movie.objects.bulk_create([Movie(title=f'Film {i:02}', genre='Comedy') for i in range(30)])
        response = self.client.get(reverse('movie_list'), {'q': 'Film', 'genre': 'Comedy'})
        self.assertEqual(len(response.context['movies']), 24)
        self.assertContains(response, 'page=2')
        self.assertNotContains(response, 'Example Film')
        response = self.client.get(reverse('movie_list'), {'q': 'Film', 'genre': 'Comedy', 'page': '2'})
        self.assertEqual(len(response.context['movies']), 6)
        self.assertEqual(self.client.get(reverse('movie_list'), {'page': 'invalid'}).status_code, 200)
        WatchlistEntry.objects.create(user=self.user, movie=self.movie, watched=True, favorite=True)
        second = Movie.objects.get(title='Film 00')
        WatchlistEntry.objects.create(user=self.user, movie=second)
        self.client.force_login(self.user)
        response = self.client.get(reverse('watchlist'), {'status': 'watched', 'favorite': '1', 'q': 'Example'})
        self.assertEqual(len(response.context['entries']), 1)
        self.assertNotContains(response, 'Film 00')

    def test_private_review_create_edit_delete_and_validation(self):
        url = reverse('movie_detail', args=[self.movie.pk])
        self.assertEqual(self.client.post(url, {'rating': 4}).status_code, 302)
        self.assertEqual(Review.objects.count(), 0)
        foreign = Review.objects.create(user=self.other, movie=self.movie, rating=5, note='Secret from Bob')
        self.client.force_login(self.user)
        self.assertNotContains(self.client.get(url), foreign.note)
        for invalid in (0, 6):
            response = self.client.post(url, {'rating': invalid, 'note': 'invalid'})
            self.assertEqual(response.status_code, 200)
            self.assertFalse(Review.objects.filter(user=self.user).exists())
        self.client.post(url, {'rating': 4, 'note': '<script>alert(1)</script>', 'user': self.other.pk})
        self.assertContains(self.client.get(url), '&lt;script&gt;')
        self.client.post(url, {'rating': 3, 'note': 'Updated'})
        self.assertEqual(Review.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Review.objects.get(user=self.user).rating, 3)
        delete_url = reverse('delete_review', args=[self.movie.pk])
        self.assertEqual(self.client.get(delete_url).status_code, 405)
        self.client.post(delete_url)
        self.assertFalse(Review.objects.filter(user=self.user).exists())
        self.assertTrue(Review.objects.filter(pk=foreign.pk).exists())

    def test_database_rejects_out_of_range_rating(self):
        for rating in (0, 6):
            with self.assertRaises(IntegrityError), transaction.atomic():
                Review.objects.create(user=self.user, movie=self.movie, rating=rating)

    def test_csv_import_is_repeatable_and_validates_before_writing(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'movies.csv'
            path.write_text('title,year,genre,description\nImported,2000,Drama,Original note\n', encoding='utf-8')
            call_command('import_movies', str(path), stdout=StringIO())
            call_command('import_movies', str(path), stdout=StringIO())
            self.assertEqual(Movie.objects.filter(title='Imported').count(), 1)
            path.write_text('title,year,genre,description\nValid,2001,,\nBroken,abc,,\n', encoding='utf-8')
            with self.assertRaises(CommandError):
                call_command('import_movies', str(path), stdout=StringIO())
            self.assertFalse(Movie.objects.filter(title='Valid').exists())
