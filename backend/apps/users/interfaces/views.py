from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class UserListView(APIView):
    def get(self, request: Request) -> Response:
        raise NotImplementedError


class MeView(APIView):
    def get(self, request: Request) -> Response:
        raise NotImplementedError
