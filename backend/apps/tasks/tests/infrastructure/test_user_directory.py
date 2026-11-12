import pytest

from apps.tasks.infrastructure.user_directory import DjangoUserDirectory
from apps.users.tests.factories import make_user

pytestmark = pytest.mark.django_db


@pytest.fixture
def directory() -> DjangoUserDirectory:
    return DjangoUserDirectory()


def test_an_active_user_is_accepted(directory):
    assert directory.is_active_user(make_user().pk) is True


def test_an_inactive_user_is_rejected(directory):
    assert directory.is_active_user(make_user(is_active=False).pk) is False


def test_an_unknown_user_is_rejected(directory):
    assert directory.is_active_user(999_999) is False
