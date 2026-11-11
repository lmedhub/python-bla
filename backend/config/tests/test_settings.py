import importlib
import sys
from collections.abc import Iterator
from types import ModuleType

import pytest
from django.core.exceptions import ImproperlyConfigured

ENVIRONMENT = {
    "SECRET_KEY": "k" * 50,
    "POSTGRES_HOST": "db",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "taskmanager",
    "POSTGRES_USER": "taskmanager",
    "POSTGRES_PASSWORD": "secret",
    "REDIS_URL": "redis://redis:6379/0",
    "ALLOWED_HOSTS": "api.example.com, localhost",
}
SETTINGS_MODULES = ("config.settings.environment", "config.settings.local", "config.settings.prod")


@pytest.fixture
def environment(monkeypatch) -> Iterator[pytest.MonkeyPatch]:
    for name, value in ENVIRONMENT.items():
        monkeypatch.setenv(name, value)
    _forget_settings_modules()
    yield monkeypatch
    _forget_settings_modules()


def _forget_settings_modules() -> None:
    # Settings modules read the environment at import time, so each test imports them fresh.
    for name in SETTINGS_MODULES:
        sys.modules.pop(name, None)


def _load(name: str) -> ModuleType:
    return importlib.import_module(name)


def test_prod_settings_come_from_the_environment(environment):
    prod = _load("config.settings.prod")

    assert prod.DEBUG is False
    assert prod.ALLOWED_HOSTS == ["api.example.com", "localhost"]
    assert ENVIRONMENT["SECRET_KEY"] == prod.SECRET_KEY
    assert prod.DATABASES["default"]["HOST"] == "db"
    assert prod.DATABASES["default"]["ATOMIC_REQUESTS"] is True
    assert prod.CACHES["default"]["LOCATION"] == "redis://redis:6379/0"


def test_prod_settings_refuse_to_start_without_secret_key(environment):
    environment.delenv("SECRET_KEY")

    with pytest.raises(ImproperlyConfigured, match="SECRET_KEY"):
        _load("config.settings.prod")


def test_prod_settings_refuse_to_start_without_allowed_hosts(environment):
    environment.delenv("ALLOWED_HOSTS")

    with pytest.raises(ImproperlyConfigured, match="ALLOWED_HOSTS"):
        _load("config.settings.prod")


def test_local_settings_enable_debug_for_localhost_only(environment):
    local = _load("config.settings.local")

    assert local.DEBUG is True
    assert local.ALLOWED_HOSTS == ["localhost", "127.0.0.1"]
