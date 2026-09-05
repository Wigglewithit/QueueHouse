import os
from pathlib import Path
import subprocess
import sys

from django.test import SimpleTestCase


class ProductionSettingsTests(SimpleTestCase):
    def environment(self):
        env = {key: value for key, value in os.environ.items() if not key.startswith((
            'DJANGO_', 'DATABASE_URL', 'REDIS_URL', 'EMAIL_', 'DEFAULT_FROM_EMAIL', 'SUPPORT_EMAIL'
        ))}
        env.update({
            'DJANGO_ENV': 'production',
            'DJANGO_SECRET_KEY': 'tests-only-0123456789-abcdefghijklmnopqrstuvwxyz-ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            'DJANGO_ALLOWED_HOSTS': 'queuehouse.example',
            'DATABASE_URL': 'postgresql://test:test@localhost/queuehouse',
            'REDIS_URL': 'redis://localhost:6379/0',
            'EMAIL_HOST': 'smtp.example.com',
            'DEFAULT_FROM_EMAIL': 'noreply@example.com',
            'SUPPORT_EMAIL': 'support@example.com',
            'DJANGO_HSTS_INCLUDE_SUBDOMAINS': 'true',
            'DJANGO_HSTS_PRELOAD': 'true',
        })
        return env

    def check(self, env):
        return subprocess.run(
            [sys.executable, 'manage.py', 'check', '--settings=config.settings', '--deploy', '--fail-level', 'WARNING'],
            env=env, cwd=Path(__file__).resolve().parent.parent,
            capture_output=True, text=True, timeout=30,
        )

    def test_complete_production_configuration_passes_checks(self):
        result = self.check(self.environment())
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_production_refuses_missing_critical_configuration(self):
        for variable in ('DJANGO_SECRET_KEY', 'DJANGO_ALLOWED_HOSTS', 'DATABASE_URL', 'REDIS_URL', 'EMAIL_HOST', 'SUPPORT_EMAIL'):
            with self.subTest(variable=variable):
                env = self.environment()
                env.pop(variable)
                result = self.check(env)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('ImproperlyConfigured', result.stderr)

    def test_weak_secret_and_wildcard_hosts_are_rejected(self):
        for variable, value in (('DJANGO_SECRET_KEY', 'weak'), ('DJANGO_ALLOWED_HOSTS', '*'), ('DJANGO_ENV', 'typo')):
            env = self.environment()
            env[variable] = value
            self.assertNotEqual(self.check(env).returncode, 0)
