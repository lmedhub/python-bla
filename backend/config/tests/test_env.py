import pytest
from django.core.exceptions import ImproperlyConfigured

from config.env import MIN_SECRET_KEY_LENGTH, csv, required, secret_key


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
