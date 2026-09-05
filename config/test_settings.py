"""Isolated tests; CI also exercises PostgreSQL and Redis."""
import os

os.environ['DJANGO_ENV'] = 'development'
from .settings import *  # noqa: E402,F403

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
