import json

import pytest
from django.http import Http404
from django.test import RequestFactory
from rest_framework import exceptions
from rest_framework_simplejwt.exceptions import InvalidToken

from apps.core.domain.errors import (
    ConflictError,
    InvalidInputError,
    NotFoundError,
    PermissionDeniedError,
)
from apps.core.interfaces.errors import api_exception_handler, not_found_view, server_error_view


def handle(exc: Exception):
    response = api_exception_handler(exc, context={})
    assert response is not None
    return response


class TestDomainErrors:
    def test_invalid_input_is_400_with_field_messages(self):
        response = handle(InvalidInputError({"title": ["This field may not be blank."]}))

        assert response.status_code == 400
        assert response.data == {
            "code": "invalid_input",
            "detail": "Invalid input.",
            "fields": {"title": ["This field may not be blank."]},
        }

    def test_permission_denied_is_403(self):
        response = handle(PermissionDeniedError("Only the creator may delete this task."))

        assert response.status_code == 403
        assert response.data == {
            "code": "permission_denied",
            "detail": "Only the creator may delete this task.",
            "fields": {},
        }

    def test_not_found_is_404(self):
        response = handle(NotFoundError("Task not found."))

        assert response.status_code == 404
        assert response.data["code"] == "not_found"
        assert response.data["detail"] == "Task not found."

    def test_conflict_is_409(self):
        response = handle(ConflictError("Task was changed by someone else."))

        assert response.status_code == 409
        assert response.data["code"] == "conflict"


class TestFrameworkErrors:
    def test_serializer_validation_errors_use_the_same_shape(self):
        error = exceptions.ValidationError({"due_date": ["Date has wrong format."]})

        response = handle(error)

        assert response.status_code == 400
        assert response.data["code"] == "invalid_input"
        assert response.data["fields"] == {"due_date": ["Date has wrong format."]}

    def test_non_field_validation_errors_go_under_non_field_errors(self):
        response = handle(exceptions.ValidationError(["Something is off."]))

        assert response.data["fields"] == {"non_field_errors": ["Something is off."]}

    def test_malformed_json_is_a_parse_error(self):
        response = handle(exceptions.ParseError())

        assert response.status_code == 400
        assert response.data["code"] == "parse_error"
        assert response.data["fields"] == {}

    def test_bad_token_is_401_without_leaking_token_details(self):
        response = handle(InvalidToken())

        assert response.status_code == 401
        assert set(response.data) == {"code", "detail", "fields"}
        assert response.data["code"] == "not_authenticated"

    def test_django_404_is_not_found(self):
        response = handle(Http404())

        assert response.status_code == 404
        assert response.data["code"] == "not_found"

    def test_throttled_is_429_and_keeps_retry_after(self):
        response = handle(exceptions.Throttled(wait=42))

        assert response.status_code == 429
        assert response.data["code"] == "throttled"
        assert response["Retry-After"] == "42"

    def test_method_not_allowed_is_405(self):
        response = handle(exceptions.MethodNotAllowed("PUT"))

        assert response.status_code == 405
        assert response.data["code"] == "method_not_allowed"

    def test_unexpected_errors_are_left_to_the_500_handler(self):
        assert api_exception_handler(RuntimeError("bug"), context={}) is None


class TestDjangoHandlers:
    def test_unknown_url_returns_json_404(self, client):
        response = client.get("/api/v1/does-not-exist")

        assert response.status_code == 404
        assert response.json() == {"code": "not_found", "detail": "Not found.", "fields": {}}

    def test_server_error_returns_json_500_without_details(self):
        response = server_error_view(RequestFactory().get("/"))

        assert response.status_code == 500
        assert json.loads(response.content) == {
            "code": "server_error",
            "detail": "Something went wrong on our side.",
            "fields": {},
        }

    @pytest.mark.parametrize("exception", [None, Http404("secret path detail")])
    def test_not_found_view_never_echoes_the_exception(self, exception):
        response = not_found_view(RequestFactory().get("/x"), exception)

        assert json.loads(response.content)["detail"] == "Not found."


class TestUnusualShapes:
    def test_a_field_error_given_as_a_single_string_becomes_a_list(self):
        response = handle(exceptions.ValidationError({"title": "Too long."}))

        assert response.data["fields"] == {"title": ["Too long."]}

    def test_an_error_body_without_detail_still_gets_a_message(self):
        response = handle(exceptions.APIException({"unexpected": "shape"}))

        assert response.status_code == 500
        assert response.data == {"code": "error", "detail": "Request failed.", "fields": {}}
