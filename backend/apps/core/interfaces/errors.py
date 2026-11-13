from typing import Any

from django.http import HttpRequest, JsonResponse
from rest_framework.response import Response


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    raise NotImplementedError


def not_found_view(request: HttpRequest, exception: Exception | None = None) -> JsonResponse:
    raise NotImplementedError


def server_error_view(request: HttpRequest) -> JsonResponse:
    raise NotImplementedError
