from datetime import UTC, tzinfo
from zoneinfo import ZoneInfo

from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.request import Request

TIME_ZONE_HEADER = "X-Timezone"


def current_user_id(request: Request) -> int:
    """The signed-in user's id, as the int the use cases expect.

    Views are protected by IsAuthenticated, so an anonymous user here means a view was
    misconfigured. Answer 401 rather than passing None into a use case.
    """
    user_id = request.user.pk
    if user_id is None:
        raise NotAuthenticated()
    return int(user_id)


def request_time_zone(request: Request) -> tzinfo:
    """The caller's IANA time zone (e.g. "America/Sao_Paulo"); UTC when not sent."""
    name = request.headers.get(TIME_ZONE_HEADER)
    if name is None:
        return UTC
    try:
        return ZoneInfo(name.strip())
    # KeyError: unknown zone (ZoneInfoNotFoundError). ValueError: malformed or path-like name.
    # OSError: some platforms raise it for a folder name such as "America".
    except (KeyError, ValueError, OSError) as error:
        message = "Unknown time zone. Send an IANA name such as Europe/Lisbon."
        raise ValidationError({TIME_ZONE_HEADER: [message]}) from error
