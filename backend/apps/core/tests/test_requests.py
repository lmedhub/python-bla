from datetime import UTC
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.request import Request

from apps.core.interfaces.requests import current_user_id, request_time_zone


def request_for(user):
    return SimpleNamespace(user=user)


def test_returns_the_signed_in_users_id():
    assert current_user_id(request_for(SimpleNamespace(pk=7))) == 7


def test_an_anonymous_user_is_401_not_a_none_id():
    with pytest.raises(NotAuthenticated):
        current_user_id(request_for(AnonymousUser()))


def request_with(**headers) -> Request:
    return Request(RequestFactory().get("/", headers=headers))


class TestRequestTimeZone:
    def test_defaults_to_utc_when_the_header_is_missing(self):
        assert request_time_zone(request_with()) is UTC

    def test_reads_an_iana_zone_name(self):
        zone = request_time_zone(request_with(**{"X-Timezone": "America/Sao_Paulo"}))

        assert zone == ZoneInfo("America/Sao_Paulo")

    @pytest.mark.parametrize(
        "name", ["Mars/Olympus_Mons", "../../etc/passwd", "UTC+3", " ", "America"]
    )
    def test_rejects_unknown_or_malformed_names_as_a_400_on_the_header(self, name):
        with pytest.raises(ValidationError) as error:
            request_time_zone(request_with(**{"X-Timezone": name}))

        assert list(error.value.detail) == ["X-Timezone"]
