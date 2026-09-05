import re
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from movies.models import Movie, Review, WatchlistEntry


class AccountTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(
            'alice', email='alice@example.com', password='TestPassword-246!'
        )

    def test_signup_message_login_next_and_logout(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newuser', 'email': 'new@example.com',
            'password1': 'StrongPassword-987!', 'password2': 'StrongPassword-987!',
        }, follow=True)
        self.assertContains(response, 'Account created successfully')
        response = self.client.post(reverse('login'), {
            'username': 'newuser', 'password': 'StrongPassword-987!', 'next': '/watchlist/',
        })
        self.assertRedirects(response, '/watchlist/')
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('logout')), reverse('home'))
        response = self.client.post(reverse('login'), {
            'username': 'newuser', 'password': 'StrongPassword-987!', 'next': 'https://evil.example/',
        })
        self.assertEqual(response.url, reverse('movie_list'))

    def test_password_reset_complete_and_token_cannot_be_reused(self):
        response = self.client.post(reverse('password_reset'), {'email': self.user.email})
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        reset_url = re.search(r'http://testserver(/\S+)', mail.outbox[0].body).group(1)
        response = self.client.get(reset_url)
        self.assertEqual(response.status_code, 302)
        form_url = response.url
        self.assertContains(self.client.get(form_url), 'Choose a new password')
        response = self.client.post(form_url, {
            'new_password1': 'ReplacementPassword-321!', 'new_password2': 'ReplacementPassword-321!',
        })
        self.assertRedirects(response, reverse('password_reset_complete'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ReplacementPassword-321!'))
        self.assertContains(self.client.get(reset_url), 'expired or has already been used')
        self.client.post(reverse('password_reset'), {'email': 'missing@example.com'})
        self.assertEqual(len(mail.outbox), 1)

    def test_rate_limits_signup_login_reset_and_admin(self):
        for name, payload, limit in (
            ('signup', {}, 5),
            ('login', {'username': 'alice', 'password': 'wrong'}, 10),
            ('password_reset', {'email': 'missing@example.com'}, 5),
            ('admin:login', {'username': 'alice', 'password': 'wrong'}, 10),
        ):
            cache.clear()
            url = reverse(name)
            for _ in range(limit):
                self.assertNotEqual(self.client.post(url, payload).status_code, 429)
            response = self.client.post(url, payload)
            self.assertEqual(response.status_code, 429)
            self.assertIn('Retry-After', response)
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_account_deletion_requires_password_and_preserves_other_accounts(self):
        movie = Movie.objects.create(title='Shared movie')
        WatchlistEntry.objects.create(user=self.user, movie=movie)
        Review.objects.create(user=self.user, movie=movie, rating=3)
        other = get_user_model().objects.create_user('bob', password='TestPassword-246!')
        entry = WatchlistEntry.objects.create(user=other, movie=movie)
        url = reverse('delete_account')
        self.assertEqual(self.client.post(url).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.post(url, {'password': 'wrong'})
        self.assertTrue(get_user_model().objects.filter(pk=self.user.pk).exists())
        response = self.client.post(url, {'password': 'TestPassword-246!'}, follow=True)
        self.assertContains(response, 'have been deleted')
        self.assertFalse(get_user_model().objects.filter(pk=self.user.pk).exists())
        self.assertFalse(Review.objects.exists())
        self.assertTrue(WatchlistEntry.objects.filter(pk=entry.pk).exists())
        self.assertTrue(Movie.objects.filter(pk=movie.pk).exists())
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_help_pages_and_not_found(self):
        for name in ('privacy', 'support'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertContains(self.client.get('/does-not-exist/'), 'Page not found', status_code=404)
