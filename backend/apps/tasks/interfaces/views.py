from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class TaskCollectionView(APIView):
    def get(self, request: Request) -> Response:
        raise NotImplementedError

    def post(self, request: Request) -> Response:
        raise NotImplementedError


class TaskDetailView(APIView):
    def get(self, request: Request, task_id: int) -> Response:
        raise NotImplementedError

    def patch(self, request: Request, task_id: int) -> Response:
        raise NotImplementedError

    def delete(self, request: Request, task_id: int) -> Response:
        raise NotImplementedError
