from django.contrib import admin
from .models import Movie, WatchlistEntry, Review

admin.site.register(Movie)
admin.site.register(WatchlistEntry)
admin.site.register(Review)