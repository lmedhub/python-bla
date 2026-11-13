"""Fixtures shared by the API tests of every feature."""

from collections.abc import Callable

import pytest
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken


@pytest.fixture
def api_client() -> APIClient:
    # Throttle counters live in Redis and would leak between tests without this.
    # Only API tests use this fixture, so domain tests still run without Redis.
    cache.clear()
    return APIClient()


@pytest.fixture
def login_as(api_client: APIClient) -> Callable[[AbstractBaseUser], APIClient]:
    def authenticate(user: AbstractBaseUser) -> APIClient:
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
        return api_client

    return authenticate
