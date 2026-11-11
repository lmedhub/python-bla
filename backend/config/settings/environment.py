"""Settings that come from environment variables. Shared by local and prod; never by tests."""

from config.env import required, secret_key

from .base import postgres, redis_cache

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
