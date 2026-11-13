"""Login, refresh and logout (ADR 0003).

The access token goes in the response body and lives only in the frontend's memory.
The refresh token goes in an HttpOnly cookie that JavaScript cannot read.
"""

from contextlib import suppress

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.interfaces.throttling import LoginThrottle
from apps.users.interfaces import container
from apps.users.interfaces.serializers import LoginSerializer, SessionSerializer

INVALID_CREDENTIALS = "Invalid email or password."
SESSION_EXPIRED = "Your session has expired. Please log in again."


class _CredentialView(APIView):
    """Login, refresh and logout use credentials or the refresh cookie, never a bearer token.

    No authenticators, so a stale Authorization header can never block a login.
    """

    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get_authenticate_header(self, request: Request) -> str:
        # Without authenticators, DRF would turn our 401 responses into 403s.
        return 'Bearer realm="api"'


class LoginView(_CredentialView):
    throttle_classes = (LoginThrottle,)

    def post(self, request: Request) -> Response:
        credentials = LoginSerializer(data=request.data)
        credentials.is_valid(raise_exception=True)
        user = authenticate(
            request,
            email=credentials.validated_data["email"],
            password=credentials.validated_data["password"],
        )
        # One message for unknown email, wrong password and inactive user: no account probing.
        if user is None:
            raise AuthenticationFailed(INVALID_CREDENTIALS)

        refresh = RefreshToken.for_user(user)
        return _session_response(str(refresh.access_token), str(refresh), user.pk)


class RefreshView(_CredentialView):
    def post(self, request: Request) -> Response:
        cookie = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if not cookie:
            raise NotAuthenticated(SESSION_EXPIRED)

        rotation = TokenRefreshSerializer(data={"refresh": cookie})
        try:
            rotation.is_valid(raise_exception=True)
        # TokenError: expired, tampered or blacklisted. ObjectDoesNotExist: simplejwt 5.5.1
        # looks the user up without handling a deleted user, which would otherwise be a 500.
        except (TokenError, ObjectDoesNotExist) as error:
            raise AuthenticationFailed(SESSION_EXPIRED) from error

        new_refresh = rotation.validated_data["refresh"]
        # We just issued this token ourselves, so reading its claims needs no second check.
        user_id = RefreshToken(new_refresh, verify=False)[jwt_settings.USER_ID_CLAIM]
        return _session_response(rotation.validated_data["access"], new_refresh, int(user_id))


class LogoutView(_CredentialView):
    def post(self, request: Request) -> Response:
        cookie = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if cookie:
            # Already blacklisted, expired or garbage: the session is over either way.
            with suppress(TokenError):
                # simplejwt annotates this argument as Token, but it takes the encoded string
                # (its own refresh serializer does the same).
                RefreshToken(cookie).blacklist()  # type: ignore[arg-type]

        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(
            settings.REFRESH_COOKIE_NAME, path=settings.REFRESH_COOKIE_PATH, samesite="Strict"
        )
        return response


def _session_response(access: str, refresh: str, user_id: int) -> Response:
    user = container.get_user().execute(user_id)
    response = Response(SessionSerializer({"access": access, "user": user}).data)
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        refresh,
        max_age=int(jwt_settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
        path=settings.REFRESH_COOKIE_PATH,
        secure=settings.REFRESH_COOKIE_SECURE,
        httponly=True,
        samesite="Strict",
    )
    return response
