from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.interfaces import container
from apps.core.interfaces.schema import HealthSerializer


def _word(is_up: bool) -> str:
    return "up" if is_up else "down"


class HealthView(APIView):
    # Docker and load balancers call this without a token, and it must never be throttled.
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = ()

    @extend_schema(
        summary="Liveness and readiness",
        auth=[],
        responses={
            200: OpenApiResponse(
                HealthSerializer, description='"ok", or "degraded" without Redis.'
            ),
            503: OpenApiResponse(HealthSerializer, description="The database is down."),
        },
    )
    def get(self, request: Request) -> Response:
        report = container.health_report()
        is_down = report.status == "down"
        return Response(
            {
                "status": report.status,
                "checks": {"database": _word(report.database), "redis": _word(report.redis)},
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE if is_down else status.HTTP_200_OK,
        )
