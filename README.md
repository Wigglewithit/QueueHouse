# QueueHouse

QueueHouse is a Django movie-watchlist beta. Users can browse a shared catalog, keep a private watchlist, mark films watched or favorite, and save private 1–5 ratings and notes.

## Implemented

- Registration, login/logout, password-reset email and password-confirmed account deletion.
- Staff-only catalog creation and a validated, repeatable CSV catalog import.
- Title search, genre filtering, pagination, watched and favorites filters.
- Private ratings and notes with ownership checks and database rating constraints.
- POST/CSRF protection, signup/login/reset throttling and environment-based production settings.
- Responsive templates, visible feedback, privacy/support pages and error pages.

External movie APIs, posters, recommendations, public reviews, friends and activity feeds are **not implemented**. They are outside this beta's scope. The starter CSV contains only basic movie facts, with no copied artwork or descriptions.

## Local setup (Python 3.12+)

Windows PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
$env:DJANGO_ENV = 'development'
.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py import_movies data/starter_movies.csv
.venv/Scripts/python manage.py createsuperuser
.venv/Scripts/python manage.py runserver
```

macOS/Linux:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export DJANGO_ENV=development
python manage.py migrate
python manage.py import_movies data/starter_movies.csv
python manage.py createsuperuser
python manage.py runserver
```

Visit http://127.0.0.1:8000/. Local development uses SQLite and an in-process cache. Reset emails print to the server terminal; no email is sent. Environment variables must be exported; `.env.example` is a reference and is not automatically loaded.

## Verification

```powershell
.venv/Scripts/python manage.py test --settings=config.test_settings
$env:DJANGO_ENV = 'development'
.venv/Scripts/python manage.py makemigrations --check --dry-run
.venv/Scripts/python manage.py collectstatic --noinput
.venv/Scripts/python -m pip check
```

GitHub Actions runs tests on PostgreSQL and Redis, checks for missing migrations, and validates production settings and static collection. Local tests use SQLite unless DATABASE_URL is provided.

## Deploying

Read [DEPLOYMENT.md](DEPLOYMENT.md). Production is the default and refuses to boot without required configuration. Do not use `runserver` for public traffic.

The repository includes a Linux Dockerfile and Gunicorn entry point. Deployments, provider accounts, DNS, real email delivery, backup schedules and monitoring must be configured by the operator. No infrastructure is provisioned automatically.

## Catalog

`python manage.py import_movies path/to/movies.csv` accepts UTF-8 columns `title,year,genre,description`. It validates the whole file before writing and skips existing title/year pairs without overwriting edits. Run a single import process at a time. Curate metadata and verify rights before adding external descriptions or posters.

## Source reuse

No open-source license has been granted. The owner must choose a license before inviting reuse or distribution. Public visibility on GitHub does not itself grant an open-source license.
