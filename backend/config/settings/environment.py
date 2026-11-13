"""Settings that come from environment variables. Shared by local and prod; never by tests."""

from config.env import optional_int, required, secret_key

from .base import REST_FRAMEWORK as BASE_REST_FRAMEWORK
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

# 1 behind nginx (Docker), unset when Django is reached directly (runserver).
REST_FRAMEWORK = {**BASE_REST_FRAMEWORK, "NUM_PROXIES": optional_int("NUM_PROXIES")}
