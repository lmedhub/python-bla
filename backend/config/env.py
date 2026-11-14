"""Read configuration from environment variables. Missing values fail at startup, not later."""

import os

from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured

# Django recommends 50+ characters; PyJWT also warns on short HMAC keys.
MIN_SECRET_KEY_LENGTH = 50


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"Environment variable {name} is required.")
    return value


def secret_key() -> str:
    key = required("SECRET_KEY")
    if len(key) < MIN_SECRET_KEY_LENGTH:
        raise ImproperlyConfigured(
            f"SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} characters long."
        )
    return key


def optional_int(name: str) -> int | None:
    value = os.environ.get(name, "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError as error:
        raise ImproperlyConfigured(
            f"Environment variable {name} must be a whole number."
        ) from error


def csv(name: str) -> list[str]:
    return [item.strip() for item in required(name).split(",") if item.strip()]


def cron(name: str, default: str) -> crontab:
    """A standard 5-field cron expression ("minute hour day month weekday"), checked at startup."""
    # from_string splits on single spaces, so collapse repeated ones first.
    value = " ".join(os.environ.get(name, default).split())
    try:
        return crontab.from_string(value)
    except ValueError as error:
        raise ImproperlyConfigured(
            f'Environment variable {name} must be a 5-field cron expression, like "0 8 * * *".'
        ) from error


_TRUE = {"true", "1"}
_FALSE = {"false", "0"}


def optional_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name, "").strip().lower()
    if not value:
        return default
    if value in _TRUE | _FALSE:
        return value in _TRUE
    raise ImproperlyConfigured(f"Environment variable {name} must be true or false.")
