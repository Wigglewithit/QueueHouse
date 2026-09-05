"""Environment-based settings. Production is the safe default."""
import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
ENVIRONMENT = os.environ.get('DJANGO_ENV', 'production')
if ENVIRONMENT not in {'development', 'production'}:
    raise ImproperlyConfigured('DJANGO_ENV must be development or production.')
DEBUG = ENVIRONMENT == 'development'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('Set DJANGO_SECRET_KEY in production.')
    SECRET_KEY = 'django-insecure-local-development-only-never-use-in-production'
if not DEBUG and (len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith('django-insecure-')):
    raise ImproperlyConfigured('Production requires a strong, newly generated secret key.')
ALLOWED_HOSTS = [host.strip() for host in os.environ.get(
    'DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1' if DEBUG else ''
).split(',') if host.strip()]
if not DEBUG and (not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS):
    raise ImproperlyConfigured('Set explicit DJANGO_ALLOWED_HOSTS in production.')
CSRF_TRUSTED_ORIGINS = [value.strip() for value in os.environ.get(
    'DJANGO_CSRF_TRUSTED_ORIGINS', ''
).split(',') if value.strip()]

INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'movies', 'accounts',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'config.context_processors.site_settings',
    ]},
}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
database_url = os.environ.get('DATABASE_URL', '')
if database_url:
    DATABASES['default'] = dj_database_url.parse(database_url, conn_max_age=60, conn_health_checks=True)
if not DEBUG and DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
    raise ImproperlyConfigured('Set DATABASE_URL to a persistent PostgreSQL database in production.')
redis_url = os.environ.get('REDIS_URL', '')
if not DEBUG and not redis_url:
    raise ImproperlyConfigured('Set REDIS_URL for shared production rate limits.')
CACHES = {'default': {
    'BACKEND': 'django.core.cache.backends.redis.RedisCache' if redis_url else 'django.core.cache.backends.locmem.LocMemCache',
    'LOCATION': redis_url or 'queuehouse-development', 'KEY_PREFIX': 'queuehouse',
}}
# Only select a proxy header if the trusted edge overwrites it on every request.
RATELIMIT_IP_META_KEY = os.environ.get('RATELIMIT_IP_META_KEY', 'REMOTE_ADDR')
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('DJANGO_HSTS_INCLUDE_SUBDOMAINS', 'false').lower() == 'true'
SECURE_HSTS_PRELOAD = os.environ.get('DJANGO_HSTS_PRELOAD', 'false').lower() == 'true'
if os.environ.get('DJANGO_TRUST_PROXY', 'false').lower() == 'true':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() == 'true'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'false').lower() == 'true'
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'queuehouse@localhost' if DEBUG else '')
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', '')
if not DEBUG and not all([EMAIL_HOST, DEFAULT_FROM_EMAIL, SUPPORT_EMAIL]):
    raise ImproperlyConfigured('Set EMAIL_HOST, DEFAULT_FROM_EMAIL and SUPPORT_EMAIL in production.')
PASSWORD_RESET_TIMEOUT = 3600
LOGGING = {
    'version': 1, 'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
LOGIN_REDIRECT_URL = 'movie_list'
LOGOUT_REDIRECT_URL = 'home'
