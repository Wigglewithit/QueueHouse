from django import forms
from .models import Movie, Review


class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ['title', 'year', 'genre', 'description']


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'note']
        labels = {'rating': 'Your rating (1 to 5)', 'note': 'Your private notes'}
        widgets = {'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}), 'note': forms.Textarea(attrs={'rows': 4})}
