from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.interfaces.requests import current_user_id
from apps.core.interfaces.schema import error_responses
from apps.users.interfaces import container
from apps.users.interfaces.serializers import UserSerializer


class UserListView(APIView):
    """Active users for the assignee picker. Not paginated: one team fits in one response."""

    @extend_schema(
        summary="List active users",
        responses={200: UserSerializer(many=True), **error_responses(401, 429)},
    )
    def get(self, request: Request) -> Response:
        users = container.list_active_users().execute()
        return Response(UserSerializer(users, many=True).data)


class MeView(APIView):
    @extend_schema(
        summary="The signed-in user",
        responses={200: UserSerializer, **error_responses(401, 429)},
    )
    def get(self, request: Request) -> Response:
        user = container.get_user().execute(current_user_id(request))
        return Response(UserSerializer(user).data)
