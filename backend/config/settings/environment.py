"""Settings that come from environment variables. Shared by local and prod; never by tests."""

from config.env import cron, optional_bool, optional_int, required, secret_key

from .base import REST_FRAMEWORK as BASE_REST_FRAMEWORK
from .base import overdue_digest_schedule, postgres, redis_cache, smtp_mailer

SECRET_KEY = secret_key()

DATABASES = postgres(
    host=required("POSTGRES_HOST"),
    port=required("POSTGRES_PORT"),
    name=required("POSTGRES_DB"),
    user=required("POSTGRES_USER"),
    password=required("POSTGRES_PASSWORD"),
)

REDIS_URL = required("REDIS_URL")
CACHES = redis_cache(REDIS_URL)
CELERY_BROKER_URL = REDIS_URL
# Read by Celery beat only. Times are UTC (CELERY_TIMEZONE).
CELERY_BEAT_SCHEDULE = overdue_digest_schedule(cron("OVERDUE_DIGEST_CRON", default="0 8 * * *"))

# 25 is the SMTP default; Mailpit listens on 1025.
MAILERS = smtp_mailer(host=required("EMAIL_HOST"), port=optional_int("EMAIL_PORT") or 25)

# 1 behind nginx (Docker), unset when Django is reached directly (runserver).
REST_FRAMEWORK = {**BASE_REST_FRAMEWORK, "NUM_PROXIES": optional_int("NUM_PROXIES")}

# Secure by default. Browsers accept Secure cookies on http://localhost (Safari excepted); set
# false only for a demo on plain http elsewhere (README).
REFRESH_COOKIE_SECURE = optional_bool("REFRESH_COOKIE_SECURE", default=True)
