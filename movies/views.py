from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Exists, F, OuterRef
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import MovieForm, ReviewForm
from .models import Movie, Review, WatchlistEntry


def home(request):
    return render(request, 'movies/home.html')


def movie_list(request):
    query = request.GET.get('q', '').strip()[:200]
    genre = request.GET.get('genre', '').strip()[:100]
    movies = Movie.objects.all().order_by('title', 'pk')
    if query:
        movies = movies.filter(title__icontains=query)
    if genre:
        movies = movies.filter(genre__iexact=genre)
    if request.user.is_authenticated:
        movies = movies.annotate(in_watchlist=Exists(
            WatchlistEntry.objects.filter(user=request.user, movie_id=OuterRef('pk'))
        ))
    page = Paginator(movies, 24).get_page(request.GET.get('page'))
    return render(request, 'movies/movie_list.html', {
        'movies': page, 'page_obj': page, 'q': query, 'genre': genre,
        'genres': Movie.objects.exclude(genre='').values_list('genre', flat=True).distinct().order_by('genre'),
    })


@login_required
def watchlist_view(request):
    query = request.GET.get('q', '').strip()[:200]
    status = request.GET.get('status', '')
    favorite = request.GET.get('favorite') == '1'
    entries = WatchlistEntry.objects.filter(user=request.user).select_related('movie').order_by('-added_at', '-pk')
    if query:
        entries = entries.filter(movie__title__icontains=query)
    if status in {'watched', 'unwatched'}:
        entries = entries.filter(watched=status == 'watched')
    if favorite:
        entries = entries.filter(favorite=True)
    page = Paginator(entries, 24).get_page(request.GET.get('page'))
    return render(request, 'movies/watchlist.html', {
        'entries': page, 'page_obj': page, 'q': query, 'status': status, 'favorite': favorite,
    })


@login_required
@require_POST
def toggle_watched(request, entry_id):
    entry = get_object_or_404(WatchlistEntry, pk=entry_id, user=request.user)
    WatchlistEntry.objects.filter(pk=entry.pk).update(watched=~F('watched'))
    messages.success(request, 'Watch status updated.')
    return redirect('watchlist')


@login_required
@require_POST
def toggle_favorite(request, entry_id):
    entry = get_object_or_404(WatchlistEntry, pk=entry_id, user=request.user)
    WatchlistEntry.objects.filter(pk=entry.pk).update(favorite=~F('favorite'))
    messages.success(request, 'Favorite updated.')
    return redirect('watchlist')


@login_required
@require_POST
def remove_from_watchlist(request, entry_id):
    entry = get_object_or_404(WatchlistEntry, pk=entry_id, user=request.user)
    entry.delete()
    messages.success(request, 'Movie removed from your watchlist. Any private notes are kept on the movie page.')
    return redirect('watchlist')


@login_required
@require_POST
def add_to_watchlist(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    _, created = WatchlistEntry.objects.get_or_create(user=request.user, movie=movie)
    if created:
        messages.success(request, f'{movie.title} added to your watchlist.')
    else:
        messages.info(request, 'This movie is already in your watchlist.')
    return redirect('movie_list')


@login_required
@require_http_methods(['GET', 'POST'])
def add_movie(request):
    if not request.user.is_staff:
        raise PermissionDenied
    form = MovieForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Movie added to the catalog.')
        return redirect('movie_list')
    return render(request, 'movies/add_movie.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    review = None
    in_watchlist = False
    if request.user.is_authenticated:
        review = Review.objects.filter(user=request.user, movie=movie).first()
        in_watchlist = WatchlistEntry.objects.filter(user=request.user, movie=movie).exists()
    if request.method == 'POST' and not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.path)
    form = ReviewForm(request.POST if request.method == 'POST' else None, instance=review)
    if request.method == 'POST' and form.is_valid():
        Review.objects.update_or_create(
            user=request.user, movie=movie,
            defaults={'rating': form.cleaned_data['rating'], 'note': form.cleaned_data['note']},
        )
        messages.success(request, 'Your private rating and notes have been saved.')
        return redirect('movie_detail', movie_id=movie.pk)
    return render(request, 'movies/movie_detail.html', {
        'movie': movie, 'form': form, 'review': review, 'in_watchlist': in_watchlist,
    })


@login_required
@require_POST
def delete_review(request, movie_id):
    review = get_object_or_404(Review, user=request.user, movie_id=movie_id)
    review.delete()
    messages.success(request, 'Your rating and notes have been deleted.')
    return redirect('movie_detail', movie_id=movie_id)
