from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie
from django.http import HttpResponseNotAllowed
from .forms import MovieForm
from django.contrib.auth.decorators import login_required
from .models import WatchlistEntry, Movie

def home(request):
    return render(request, 'movies/home.html')
@login_required
def watchlist_view(request):
    entries = WatchlistEntry.objects.filter(user=request.user).select_related("movie")
    return render(request, "movies/watchlist.html", {"entries": entries})


def movie_list(request):
    movies = Movie.objects.all().order_by('title')
    return render(request, 'movies/movie_list.html', {'movies': movies})


@login_required
def toggle_watched(request, entry_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    entry = get_object_or_404(WatchlistEntry, id=entry_id, user=request.user)
    entry.watched = not entry.watched
    entry.save()

    return redirect("watchlist")

@login_required
def remove_from_watchlist(request, entry_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    entry = get_object_or_404(WatchlistEntry, id=entry_id, user=request.user)
    entry.delete()

    return redirect("watchlist")

@login_required
def toggle_favorite(request, entry_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    entry = get_object_or_404(WatchlistEntry, id=entry_id, user=request.user)
    entry.favorite = not entry.favorite
    entry.save()

    return redirect("watchlist")


@login_required
def add_to_watchlist(request, movie_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    movie = get_object_or_404(Movie, id=movie_id)
    WatchlistEntry.objects.get_or_create(user=request.user, movie=movie)
    return redirect("movie_list")

def add_movie(request):
    if request.method == 'POST':
        form = MovieForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('movie_list')
    else:
        form = MovieForm()

    return render(request, 'movies/add_movie.html', {'form': form})