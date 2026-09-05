# QueueHouse beta deployment

## Infrastructure and secrets

Use a Linux Python 3.12+ service with persistent PostgreSQL, private Redis and an HTTPS reverse proxy. The supplied Dockerfile builds the app; configure its environment through your hosting provider. Do not put credentials in source control.

Required production environment:

| Variable | Value |
| --- | --- |
| DJANGO_ENV | production |
| DJANGO_SECRET_KEY | A newly generated random secret, at least 50 characters |
| DJANGO_ALLOWED_HOSTS | Comma-separated exact hostnames (no scheme or wildcard) |
| DATABASE_URL | PostgreSQL URL; use the provider's TLS connection options |
| REDIS_URL | Private Redis URL; use rediss:// when TLS is required |
| EMAIL_HOST | SMTP hostname |
| EMAIL_PORT | Usually 587 (TLS) or 465 (SSL) |
| EMAIL_HOST_USER / EMAIL_HOST_PASSWORD | SMTP credentials when required |
| EMAIL_USE_TLS / EMAIL_USE_SSL | Exactly the mode required by the provider; never both true |
| DEFAULT_FROM_EMAIL | A verified sender address |
| SUPPORT_EMAIL | A monitored support address |

Generate the secret with `python -c "import secrets; print(secrets.token_urlsafe(64))"` in a trusted terminal and save it to the provider's secret store. The old repository key must never be reused; rotate it on any existing deployment. Rotation can invalidate sessions and outstanding reset links.

Development defaults are enabled only by explicitly setting DJANGO_ENV=development. Do not set this in production.

## HTTPS and rate-limit client addresses

Terminate TLS at a trusted reverse proxy and prevent public access to Gunicorn. If using DJANGO_TRUST_PROXY=true, the proxy MUST strip and overwrite X-Forwarded-Proto from incoming requests. Otherwise leave this false and serve HTTPS directly through your infrastructure.

Rate limits use REMOTE_ADDR by default and do not trust incoming forwarding headers. Behind a proxy, set RATELIMIT_IP_META_KEY=HTTP_X_REAL_IP **only** if the trusted proxy overwrites X-Real-IP with the verified client IP on every request. For a single Nginx edge directly facing users:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;
}
```

If a CDN or additional proxy is in front, configure Nginx's trusted real-IP ranges first. Do not blindly trust a user-supplied X-Forwarded-For. Verify two independent client IPs have separate limits and spoofed headers do not bypass limits.

Production uses shared Redis so throttles work across workers. If Redis is unavailable, protected requests fail closed; monitor this dependency. Development's local-memory cache is for a single process only.

HTTPS redirect and secure cookies are enabled in production. HSTS is set to one year. Set DJANGO_HSTS_INCLUDE_SUBDOMAINS=true only after all relevant subdomains support HTTPS. Set DJANGO_HSTS_PRELOAD=true only after reviewing the implications of browser preloading. These flags default to false intentionally; Django reports security.W005 and security.W021 until enabled. Review those two advisories rather than weakening the other checks.

DJANGO_CSRF_TRUSTED_ORIGINS may contain comma-separated HTTPS origins if your architecture requires additional trusted origins. Standard same-origin deployment needs no extra origins.

## Release procedure

1. Back up an existing database and test restoration to an isolated database.
2. Install the pinned requirements or build the Docker image. Apply environment variables.
3. Run `python manage.py migrate --plan` and then `python manage.py migrate` as a single release job.
4. Run `python manage.py collectstatic --noinput` (the container does this at startup).
5. Run `python manage.py check --deploy`. Resolve every issue; the two HSTS advisories above require a domain-specific decision.
6. Run `python manage.py import_movies data/starter_movies.csv` once if a starter catalog is wanted. Existing matches are skipped.
7. Run `python manage.py createsuperuser` in a trusted terminal.
8. Start `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 30 --error-logfile -`. Set the bind port for your host.
9. Check the app through the real HTTPS hostname. Test signup, logout/login, catalog search, watchlist actions, a real reset email, notes and account deletion.
10. Test narrow screens, keyboard navigation, error pages and admin permissions before inviting beta users.

The rating migration refuses to run if existing ratings fall outside 1–5. Inspect and correct those records deliberately after backup; it does not silently delete or rewrite user data.

Do not copy an old SQLite database into an ephemeral container. Migrate existing user data into PostgreSQL with a rehearsed export/import process and verify record counts before switching traffic.

## Operations and remaining launch decisions

- Enable database backups at the provider, choose a retention period and rehearse restoration. Restrict backup access and use encryption.
- Configure uptime and application-error alerts. Django writes errors to stderr; connect your host's logs to a monitored alert channel. Avoid logging POST bodies, passwords, cookies or password-reset URLs.
- Track the deployed commit/image. Before a rollback, assess migration compatibility and use a tested database restore if necessary.
- Schedule `python manage.py clearsessions` daily.
- Verify SMTP delivery, sender verification, and your provider's SPF/DKIM requirements. Test reset links through the actual public domain.
- Complete privacy information with the operator identity, actual providers, log/backup retention periods and applicable audience requirements before launch. The included page describes application behavior; provider-specific details cannot be inferred from this repository.
- Establish how deletion requests remain honored when restoring backups. A restore can otherwise resurrect previously deleted accounts.
- Choose a code license if you intend open-source reuse. This change does not grant redistribution rights.
- Keep dependency pins updated and run CI after upgrades.
- External metadata, poster licensing, public-review moderation and recommendations are later product decisions.

No DNS, hosting, paid services, email credentials, monitoring subscriptions or public deployment are created by these source changes.
