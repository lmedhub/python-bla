import pytest
from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured

from config.env import MIN_SECRET_KEY_LENGTH, cron, csv, optional_int, required, secret_key


def test_required_returns_the_value(monkeypatch):
    monkeypatch.setenv("SOME_SETTING", "value")

    assert required("SOME_SETTING") == "value"


def test_required_fails_when_missing(monkeypatch):
    monkeypatch.delenv("SOME_SETTING", raising=False)

    with pytest.raises(ImproperlyConfigured, match="SOME_SETTING"):
        required("SOME_SETTING")


def test_required_fails_when_blank(monkeypatch):
    monkeypatch.setenv("SOME_SETTING", "   ")

    with pytest.raises(ImproperlyConfigured, match="SOME_SETTING"):
        required("SOME_SETTING")


def test_secret_key_fails_when_missing(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ImproperlyConfigured, match="SECRET_KEY"):
        secret_key()


def test_secret_key_fails_when_too_short(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x" * (MIN_SECRET_KEY_LENGTH - 1))

    with pytest.raises(ImproperlyConfigured, match="at least"):
        secret_key()


def test_secret_key_accepts_a_long_enough_key(monkeypatch):
    key = "x" * MIN_SECRET_KEY_LENGTH
    monkeypatch.setenv("SECRET_KEY", key)

    assert secret_key() == key


def test_csv_splits_and_trims(monkeypatch):
    monkeypatch.setenv("HOSTS", "a.example.com, b.example.com ,")

    assert csv("HOSTS") == ["a.example.com", "b.example.com"]


def test_optional_int_is_none_when_missing(monkeypatch):
    monkeypatch.delenv("NUM_PROXIES", raising=False)

    assert optional_int("NUM_PROXIES") is None


def test_optional_int_parses_a_number(monkeypatch):
    monkeypatch.setenv("NUM_PROXIES", " 1 ")

    assert optional_int("NUM_PROXIES") == 1


def test_optional_int_rejects_text(monkeypatch):
    monkeypatch.setenv("NUM_PROXIES", "one")

    with pytest.raises(ImproperlyConfigured, match="NUM_PROXIES"):
        optional_int("NUM_PROXIES")


def test_cron_uses_the_default_when_missing(monkeypatch):
    monkeypatch.delenv("SOME_CRON", raising=False)

    assert cron("SOME_CRON", default="0 8 * * *") == crontab.from_string("0 8 * * *")


def test_cron_reads_the_environment_and_tolerates_extra_spaces(monkeypatch):
    monkeypatch.setenv("SOME_CRON", " 30  6 * *  1-5 ")

    assert cron("SOME_CRON", default="0 8 * * *") == crontab.from_string("30 6 * * 1-5")


@pytest.mark.parametrize("value", ["0 8 * *", "0 8 * * * *", "99 8 * * *", "a b c d e"])
def test_cron_rejects_a_bad_expression(monkeypatch, value):
    monkeypatch.setenv("SOME_CRON", value)

    with pytest.raises(ImproperlyConfigured, match="SOME_CRON"):
        cron("SOME_CRON", default="0 8 * * *")
