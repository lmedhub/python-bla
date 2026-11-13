"""One error shape for every response: {"code", "detail", "fields"} (ADR 0008, decision D10)."""

from typing import Any

from django.http import HttpRequest, JsonResponse
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from apps.core.domain.errors import (
    ConflictError,
    InvalidInputError,
    NotFoundError,
    PermissionDeniedError,
)

# Stable, machine-readable codes. The frontend switches on these, never on messages.
CODES_BY_STATUS = {
    status.HTTP_400_BAD_REQUEST: "invalid_input",
    status.HTTP_401_UNAUTHORIZED: "not_authenticated",
    status.HTTP_403_FORBIDDEN: "permission_denied",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_406_NOT_ACCEPTABLE: "not_acceptable",
    status.HTTP_409_CONFLICT: "conflict",
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "unsupported_media_type",
    status.HTTP_429_TOO_MANY_REQUESTS: "throttled",
}


class Conflict(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The resource was changed by someone else."
    default_code = "conflict"


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    exc = _to_drf_exception(exc)
    # DRF's handler sets the status, the WWW-Authenticate and Retry-After headers, and marks
    # the request transaction for rollback. We only replace the body.
    response = drf_exception_handler(exc, context)
    if response is None:
        return None  # a bug, not a client error: Django's 500 handler takes over
    response.data = _body(exc, response)
    return response


def not_found_view(request: HttpRequest, exception: Exception | None = None) -> JsonResponse:
    # Never echo the exception: Django's message can include internal URL patterns.
    return JsonResponse(error_body("not_found", "Not found."), status=status.HTTP_404_NOT_FOUND)


def server_error_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        error_body("server_error", "Something went wrong on our side."),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def error_body(
    code: str, detail: str, fields: dict[str, list[str]] | None = None
) -> dict[str, Any]:
    return {"code": code, "detail": detail, "fields": fields or {}}


def _to_drf_exception(exc: Exception) -> Exception:
    if isinstance(exc, InvalidInputError):
        return exceptions.ValidationError(exc.fields)
    if isinstance(exc, PermissionDeniedError):
        return exceptions.PermissionDenied(str(exc) or None)
    if isinstance(exc, NotFoundError):
        return exceptions.NotFound(str(exc) or None)
    if isinstance(exc, ConflictError):
        return Conflict(str(exc) or None)
    return exc


def _body(exc: Exception, response: Response) -> dict[str, Any]:
    if isinstance(exc, exceptions.ValidationError):
        return error_body("invalid_input", "Invalid input.", _field_messages(response.data))
    if isinstance(exc, exceptions.ParseError):
        return error_body("parse_error", _detail(response.data))
    code = CODES_BY_STATUS.get(response.status_code, "error")
    return error_body(code, _detail(response.data))


def _detail(data: Any) -> str:
    if isinstance(data, dict) and "detail" in data:
        return str(data["detail"])
    return "Request failed."


def _field_messages(data: Any) -> dict[str, list[str]]:
    if isinstance(data, dict):
        return {field: _as_list(messages) for field, messages in data.items()}
    return {"non_field_errors": _as_list(data)}


def _as_list(messages: Any) -> list[str]:
    if isinstance(messages, list):
        return [str(message) for message in messages]
    return [str(messages)]
