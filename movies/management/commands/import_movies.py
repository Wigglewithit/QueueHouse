"""Import a reviewed CSV catalog without overwriting existing descriptions."""
import csv

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from movies.models import Movie


class Command(BaseCommand):
    help = 'Import movies from CSV (title,year,genre,description). Existing title/year pairs are skipped.'

    def add_arguments(self, parser):
        parser.add_argument('path')

    def handle(self, *args, **options):
        movies = []
        seen = set()
        try:
            with open(options['path'], encoding='utf-8-sig', newline='') as source:
                reader = csv.DictReader(source)
                if not {'title', 'year', 'genre', 'description'}.issubset(reader.fieldnames or []):
                    raise CommandError('CSV requires title,year,genre,description headers.')
                for line, row in enumerate(reader, start=2):
                    try:
                        movie = Movie(
                            title=(row['title'] or '').strip(),
                            year=int(row['year']) if row['year'] else None,
                            genre=(row['genre'] or '').strip(),
                            description=(row['description'] or '').strip(),
                        )
                        movie.full_clean()
                    except (ValueError, ValidationError) as exc:
                        raise CommandError(f'Invalid movie at line {line}: {exc}') from exc
                    key = (movie.title.casefold(), movie.year)
                    if key not in seen:
                        movies.append(movie)
                        seen.add(key)
        except (OSError, UnicodeError, csv.Error) as exc:
            raise CommandError(f'Cannot read catalog: {exc}') from exc
        created = 0
        with transaction.atomic():
            for movie in movies:
                if not Movie.objects.filter(title__iexact=movie.title, year=movie.year).exists():
                    movie.save()
                    created += 1
        self.stdout.write(self.style.SUCCESS(f'Imported {created} movies; skipped {len(movies) - created} existing movies.'))
