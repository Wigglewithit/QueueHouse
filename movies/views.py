from django.shortcuts import render
from .models import Movie


def home(request):
    return render(request, 'movies/home.html')


def movie_list(request):
    movies = Movie.objects.all().order_by('title')
    return render(request, 'movies/movie_list.html', {'movies': movies})