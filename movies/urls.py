from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('movies/', views.movie_list, name='movie_list'),
    path('movies/add/', views.add_movie, name='add_movie'),
    path("watchlist/", views.watchlist_view, name="watchlist"),
    path("watchlist/add/<int:movie_id>/", views.add_to_watchlist, name="add_to_watchlist"),
    path("watchlist/<int:entry_id>/toggle-watched/", views.toggle_watched, name="toggle_watched"),
    path("watchlist/<int:entry_id>/toggle-favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("watchlist/<int:entry_id>/remove/", views.remove_from_watchlist, name="remove_from_watchlist"),
]