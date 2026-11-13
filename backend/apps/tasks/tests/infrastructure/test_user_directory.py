import pytest

from apps.tasks.application.ports import Recipient
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


def test_active_recipients_gives_email_and_name_of_active_users_only(directory):
    alice = make_user(email="alice@example.com", name="Alice")
    gone = make_user(is_active=False)

    recipients = directory.active_recipients([alice.pk, gone.pk, 999_999])

    assert recipients == {alice.pk: Recipient(email="alice@example.com", name="Alice")}


def test_active_recipients_uses_one_query(directory, django_assert_num_queries):
    ids = [make_user().pk for _ in range(3)]

    with django_assert_num_queries(1):
        directory.active_recipients(ids)
