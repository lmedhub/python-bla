from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import NotAuthenticated

from apps.core.interfaces.requests import current_user_id


def request_for(user):
    return SimpleNamespace(user=user)


def test_returns_the_signed_in_users_id():
    assert current_user_id(request_for(SimpleNamespace(pk=7))) == 7


def test_an_anonymous_user_is_401_not_a_none_id():
    with pytest.raises(NotAuthenticated):
        current_user_id(request_for(AnonymousUser()))
