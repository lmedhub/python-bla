import pytest

from apps.users.domain.user import User
from apps.users.infrastructure.repositories import DjangoUserRepository
from apps.users.tests.factories import make_user

pytestmark = pytest.mark.django_db


@pytest.fixture
def repository() -> DjangoUserRepository:
    return DjangoUserRepository()


def test_get_returns_a_domain_user(repository):
    row = make_user(email="alice@example.com", name="Alice")

    assert repository.get(row.pk) == User(id=row.pk, email="alice@example.com", name="Alice")


def test_get_unknown_user_returns_none(repository):
    assert repository.get(999_999) is None


def test_list_active_skips_inactive_users_and_sorts_by_name(repository):
    bob = make_user(name="Bob")
    alice = make_user(name="Alice")
    make_user(name="Carol", is_active=False)

    assert [user.id for user in repository.list_active()] == [alice.pk, bob.pk]


def test_list_active_breaks_name_ties_by_id(repository):
    first = make_user(name="Sam")
    second = make_user(name="Sam")

    assert [user.id for user in repository.list_active()] == [first.pk, second.pk]
