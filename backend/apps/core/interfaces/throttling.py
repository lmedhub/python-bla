"""DRF throttles that fail open when Redis is down (ADR 0005).

Failing closed would turn a cache outage into a full API outage. While Redis is down there
is no rate limiting; every skipped check logs a warning so the outage is visible.
"""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import redis
from rest_framework.request import Request
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

if TYPE_CHECKING:
    # Type hints only: DRF imports this module while it is still defining APIView,
    # so a runtime import here would be circular.
    from rest_framework.views import APIView

logger = logging.getLogger(__name__)


def _fail_open(
    check: Callable[[Request, "APIView"], bool], request: Request, view: "APIView"
) -> bool:
    try:
        return check(request, view)
    except redis.RedisError:
        logger.warning("Rate limiting skipped: the throttle cache is unavailable.", exc_info=True)
        return True


class AnonThrottle(AnonRateThrottle):
    def allow_request(self, request: Request, view: "APIView") -> bool:
        return _fail_open(super().allow_request, request, view)


class UserThrottle(UserRateThrottle):
    def allow_request(self, request: Request, view: "APIView") -> bool:
        return _fail_open(super().allow_request, request, view)


class LoginThrottle(AnonRateThrottle):
    """5/min per client IP: slows down password guessing."""

    scope = "login"

    def allow_request(self, request: Request, view: "APIView") -> bool:
        return _fail_open(super().allow_request, request, view)
