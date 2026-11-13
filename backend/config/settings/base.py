"""Settings shared by every environment. Nothing here reads the environment."""

from datetime import timedelta
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = False
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    # Each feature's Django app is its infrastructure layer (ADR 0001).
    "apps.users.infrastructure.apps.UsersConfig",
    "apps.tasks.infrastructure.apps.TasksConfig",
]

AUTH_USER_MODEL = "users.User"

# A JSON API with JWT auth: no sessions, CSRF or template middleware needed.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

# Only the Swagger UI and ReDoc pages render templates.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
    }
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

REST_FRAMEWORK: dict[str, Any] = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "EXCEPTION_HANDLER": "apps.core.interfaces.errors.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "apps.core.interfaces.throttling.AnonThrottle",
        "apps.core.interfaces.throttling.UserThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "20/min", "user": "100/min", "login": "5/min"},
    # How many proxies sit in front of Django; behind nginx this must be 1, or every
    # client shares nginx's IP and one throttle bucket. None means "no proxy".
    "NUM_PROXIES": None,
}

# Short-lived access token kept in memory by the frontend; rotating refresh token in an
# HttpOnly cookie, blacklisted on rotation and on logout (ADR 0003).
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}
REFRESH_COOKIE_NAME = "refresh_token"
# Only the auth endpoints ever receive the cookie.
REFRESH_COOKIE_PATH = "/api/v1/auth"
REFRESH_COOKIE_SECURE = True

SPECTACULAR_SETTINGS = {
    "TITLE": "Task Manager API",
    "DESCRIPTION": (
        "Tasks with assignment, status and due dates. Sign in with POST /auth/login, then "
        'use "Authorize" with the access token. Every error has the shape '
        "{code, detail, fields}."
    ),
    "VERSION": "1.0.0",
    "SCHEMA_PATH_PREFIX": "/api/v1",
    "SERVE_INCLUDE_SCHEMA": False,
    # Separate request and response components, so generated TypeScript types do not
    # mark server-set fields (id, version, timestamps) as inputs.
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_NAME_OVERRIDES": {
        "TaskStatus": "apps.tasks.interfaces.serializers.STATUS_CHOICES",
        "ErrorCode": "apps.core.interfaces.schema.ERROR_CODES",
        "HealthStatus": "apps.core.interfaces.schema.HEALTH_STATUSES",
        "CheckStatus": "apps.core.interfaces.schema.CHECK_STATUSES",
    },
    # Pinned, never "@latest": these scripts run on the docs page (checked 2026-11-12).
    "SWAGGER_UI_DIST": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.34.0",
    "SWAGGER_UI_FAVICON_HREF": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.34.0/favicon-32x32.png",
    "REDOC_DIST": "https://cdn.jsdelivr.net/npm/redoc@2.5.4",
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
