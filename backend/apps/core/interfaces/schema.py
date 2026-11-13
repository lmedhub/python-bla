"""OpenAPI pieces shared by every feature: the error shape and its responses."""

from drf_spectacular.utils import OpenApiResponse, inline_serializer
from rest_framework import serializers

from apps.core.interfaces.errors import CODES_BY_STATUS

ERROR_CODES = sorted({*CODES_BY_STATUS.values(), "parse_error", "server_error", "error"})
HEALTH_STATUSES = ["ok", "degraded", "down"]
CHECK_STATUSES = ["up", "down"]

# inline_serializer because a declared field called "fields" would clash with
# Serializer.fields (DRF's own attribute).
ERROR = inline_serializer(
    name="Error",
    fields={
        "code": serializers.ChoiceField(choices=ERROR_CODES),
        "detail": serializers.CharField(),
        "fields": serializers.DictField(
            child=serializers.ListField(child=serializers.CharField()),
            help_text="Field name to messages. Empty unless code is invalid_input.",
        ),
    },
)

_DESCRIPTIONS = {
    400: "Invalid input. `fields` says which field and why.",
    401: "Missing, expired or invalid credentials.",
    403: "Signed in, but not allowed to do this.",
    404: "Not found.",
    409: "Changed by someone else since you read it. Reload and try again.",
    429: "Too many requests. See the Retry-After header.",
}


def error_responses(*status_codes: int) -> dict[int, OpenApiResponse]:
    return {
        code: OpenApiResponse(response=ERROR, description=_DESCRIPTIONS[code])
        for code in status_codes
    }


class HealthSerializer(serializers.Serializer[object]):
    status = serializers.ChoiceField(choices=HEALTH_STATUSES)
    checks = inline_serializer(
        name="HealthChecks",
        fields={
            "database": serializers.ChoiceField(choices=CHECK_STATUSES),
            "redis": serializers.ChoiceField(choices=CHECK_STATUSES),
        },
    )
