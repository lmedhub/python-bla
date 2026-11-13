from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class _CredentialView(APIView):
    """Login, refresh and logout use credentials or the refresh cookie, never a bearer token."""

    authentication_classes = ()
    permission_classes = (AllowAny,)


class LoginView(_CredentialView):
    def post(self, request: Request) -> Response:
        raise NotImplementedError


class RefreshView(_CredentialView):
    def post(self, request: Request) -> Response:
        raise NotImplementedError


class LogoutView(_CredentialView):
    def post(self, request: Request) -> Response:
        raise NotImplementedError
