from rest_framework.exceptions import NotAuthenticated
from rest_framework.request import Request


def current_user_id(request: Request) -> int:
    """The signed-in user's id, as the int the use cases expect.

    Views are protected by IsAuthenticated, so an anonymous user here means a view was
    misconfigured. Answer 401 rather than passing None into a use case.
    """
    user_id = request.user.pk
    if user_id is None:
        raise NotAuthenticated()
    return int(user_id)
