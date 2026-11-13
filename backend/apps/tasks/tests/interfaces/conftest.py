import pytest

from apps.tasks.interfaces import container
from apps.tasks.tests.application.constants import NOW
from apps.tasks.tests.fakes import FixedClock
from apps.users.tests.factories import make_user


@pytest.fixture(autouse=True)
def clock(monkeypatch) -> FixedClock:
    """Every API test runs on 12 Nov 2026 at 09:30 UTC, whatever the real date is."""
    fixed = FixedClock(NOW)
    monkeypatch.setattr(container, "clock", fixed)
    return fixed


@pytest.fixture
def alice():
    return make_user(name="Alice", email="alice@example.com")


@pytest.fixture
def bob():
    return make_user(name="Bob", email="bob@example.com")


@pytest.fixture
def carol():
    return make_user(name="Carol", email="carol@example.com")
