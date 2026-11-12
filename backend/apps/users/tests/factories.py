from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser
from factory.declarations import Sequence
from factory.django import DjangoModelFactory, Password


class _UserFactory(DjangoModelFactory[AbstractBaseUser]):
    class Meta:
        # A string, so other features' tests can use this factory without importing
        # users.infrastructure (the import-linter contracts would reject that).
        model = "users.User"

    email = Sequence(lambda n: f"user{n}@example.com")
    name = Sequence(lambda n: f"User {n}")
    is_active = True
    password = Password("password")


def make_user(**fields: Any) -> AbstractBaseUser:
    return _UserFactory.create(**fields)
