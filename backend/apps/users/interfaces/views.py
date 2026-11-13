from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.interfaces.requests import current_user_id
from apps.users.interfaces import container
from apps.users.interfaces.serializers import UserSerializer


class UserListView(APIView):
    """Active users for the assignee picker. Not paginated: one team fits in one response."""

    def get(self, request: Request) -> Response:
        users = container.list_active_users().execute()
        return Response(UserSerializer(users, many=True).data)


class MeView(APIView):
    def get(self, request: Request) -> Response:
        user = container.get_user().execute(current_user_id(request))
        return Response(UserSerializer(user).data)
