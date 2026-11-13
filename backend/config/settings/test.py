"""Fixed settings for the test suite and mypy.

Self-contained on purpose: `uv run pytest` works with only `docker compose up db redis`,
the same way on every machine and in CI. These values never reach a deployed environment.
"""

import os

from .base import *

SECRET_KEY = "insecure-test-only-key-0123456789abcdefghijklmnopqrstuvwxyz"  # noqa: S105

DATABASES = postgres(
    host=os.environ.get("POSTGRES_HOST", "localhost"),
    port=os.environ.get("POSTGRES_PORT", "5432"),
    name=os.environ.get("POSTGRES_DB", "taskmanager"),
    user=os.environ.get("POSTGRES_USER", "taskmanager"),
    password=os.environ.get("POSTGRES_PASSWORD", "taskmanager"),
)

# Database 1 keeps test keys away from the development data in database 0.
REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/1")
CACHES = redis_cache(REDIS_URL)
CELERY_BROKER_URL = REDIS_URL
# Django's test setup swaps every mailer for the in-memory outbox (django.core.mail.outbox).
MAILERS = smtp_mailer(host="localhost", port=1025)

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
