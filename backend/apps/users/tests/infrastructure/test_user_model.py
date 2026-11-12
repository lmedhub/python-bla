import pytest
from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError, transaction

from apps.users.tests.factories import make_user

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_create_user_normalizes_the_email_and_hashes_the_password():
    user = User.objects.create_user(email="  Alice@Example.COM ", password="s3cret!", name="Alice")

    assert user.email == "alice@example.com"
    assert user.password != "s3cret!"
    assert user.check_password("s3cret!")


def test_create_user_without_password_cannot_log_in():
    user = User.objects.create_user(email="bob@example.com", name="Bob")

    assert not user.has_usable_password()


def test_login_lookup_ignores_the_case_of_the_email():
    User.objects.create_user(email="carol@example.com", password="s3cret!", name="Carol")

    user = authenticate(email="Carol@Example.com", password="s3cret!")

    assert user is not None
    assert user.email == "carol@example.com"


def test_inactive_users_cannot_log_in():
    User.objects.create_user(
        email="dave@example.com", password="s3cret!", name="Dave", is_active=False
    )

    assert authenticate(email="dave@example.com", password="s3cret!") is None


def test_database_rejects_an_email_with_capital_letters():
    # Bypasses the manager on purpose: the constraint must hold even for raw writes.
    with pytest.raises(IntegrityError), transaction.atomic():
        make_user(email="Erin@example.com")


def test_database_rejects_a_duplicate_email():
    make_user(email="frank@example.com")

    with pytest.raises(IntegrityError), transaction.atomic():
        make_user(email="frank@example.com")
