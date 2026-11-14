import importlib
import sys
from collections.abc import Iterator
from types import ModuleType

import pytest
from celery.schedules import crontab
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
    "NUM_PROXIES": "1",
    "EMAIL_HOST": "mailpit",
    "EMAIL_PORT": "1025",
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


def test_prod_trusts_one_proxy_when_told_to(environment):
    prod = _load("config.settings.prod")

    assert prod.REST_FRAMEWORK["NUM_PROXIES"] == 1


def test_without_num_proxies_no_proxy_is_trusted(environment):
    environment.delenv("NUM_PROXIES")

    prod = _load("config.settings.prod")

    assert prod.REST_FRAMEWORK["NUM_PROXIES"] is None


def test_celery_uses_redis_as_its_broker(environment):
    prod = _load("config.settings.prod")

    assert prod.CELERY_BROKER_URL == "redis://redis:6379/0"


def test_the_overdue_digest_runs_daily_at_eight_utc_by_default(environment):
    environment.delenv("OVERDUE_DIGEST_CRON", raising=False)

    prod = _load("config.settings.prod")

    entry = prod.CELERY_BEAT_SCHEDULE["overdue-digest"]
    assert entry["task"] == "tasks.send_overdue_digests"
    assert entry["schedule"] == crontab.from_string("0 8 * * *")
    assert prod.CELERY_TIMEZONE == "UTC"


def test_the_overdue_digest_schedule_comes_from_the_environment(environment):
    environment.setenv("OVERDUE_DIGEST_CRON", "15 7 * * 1-5")

    prod = _load("config.settings.prod")

    assert prod.CELERY_BEAT_SCHEDULE["overdue-digest"]["schedule"] == crontab.from_string(
        "15 7 * * 1-5"
    )


def test_a_bad_digest_schedule_stops_startup(environment):
    environment.setenv("OVERDUE_DIGEST_CRON", "every morning")

    with pytest.raises(ImproperlyConfigured, match="OVERDUE_DIGEST_CRON"):
        _load("config.settings.prod")


def test_email_goes_to_the_configured_smtp_server(environment):
    prod = _load("config.settings.prod")

    options = prod.MAILERS["default"]["OPTIONS"]
    assert (options["host"], options["port"]) == ("mailpit", 1025)


def test_email_host_is_required(environment):
    environment.delenv("EMAIL_HOST")

    with pytest.raises(ImproperlyConfigured, match="EMAIL_HOST"):
        _load("config.settings.prod")


def test_the_refresh_cookie_is_secure_by_default(environment):
    environment.delenv("REFRESH_COOKIE_SECURE", raising=False)

    assert _load("config.settings.prod").REFRESH_COOKIE_SECURE is True


def test_the_refresh_cookie_can_be_sent_over_plain_http_when_configured(environment):
    # For a demo on plain http that is not localhost, or Safari, which ignores the
    # localhost exception for Secure cookies.
    environment.setenv("REFRESH_COOKIE_SECURE", "false")

    assert _load("config.settings.prod").REFRESH_COOKIE_SECURE is False
