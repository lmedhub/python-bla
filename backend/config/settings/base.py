"""Settings shared by every environment. Nothing here reads the environment."""

from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = False
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    # Each feature's Django app is its infrastructure layer (ADR 0001).
    "apps.users.infrastructure.apps.UsersConfig",
]

AUTH_USER_MODEL = "users.User"

# A JSON API with JWT auth: no sessions, CSRF or template middleware needed.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}


def postgres(*, host: str, port: str, name: str, user: str, password: str) -> dict[str, Any]:
    return {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": host,
            "PORT": port,
            "NAME": name,
            "USER": user,
            "PASSWORD": password,
            # One transaction per request, so use cases need no transaction code.
            "ATOMIC_REQUESTS": True,
            # Fail fast instead of hanging when the database is unreachable.
            "OPTIONS": {"connect_timeout": 3},
        }
    }


def redis_cache(url: str) -> dict[str, Any]:
    return {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": url,
            # Short timeouts so a Redis outage degrades requests instead of hanging them.
            "OPTIONS": {"socket_connect_timeout": 1, "socket_timeout": 1},
        }
    }
