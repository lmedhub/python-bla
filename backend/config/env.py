"""Read configuration from environment variables. Missing values fail at startup, not later."""

import os

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


def csv(name: str) -> list[str]:
    return [item.strip() for item in required(name).split(",") if item.strip()]
