"""HTTP in, use case call, HTTP out. No business rules and no ORM here."""

from typing import Any

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.interfaces.requests import current_user_id
from apps.tasks.application.queries import PageRequest, TaskFilter
from apps.tasks.application.use_cases import CreateTaskCommand, TaskChanges, UpdateTaskCommand
from apps.tasks.domain.task import Task, TaskStatus
from apps.tasks.interfaces import container
from apps.tasks.interfaces.pagination import paginated
from apps.tasks.interfaces.serializers import (
    TaskCreateSerializer,
    TaskListQuerySerializer,
    TaskSerializer,
    TaskUpdateSerializer,
)


class TaskCollectionView(APIView):
    def get(self, request: Request) -> Response:
        query = TaskListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data

        page = container.list_tasks().execute(
            _task_filter(params, current_user_id(request)),
            PageRequest(page=params["page"], page_size=params["page_size"]),
        )
        return Response(paginated(request, page, [_serialize(task) for task in page.items]))

    def post(self, request: Request) -> Response:
        payload = TaskCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        task = container.create_task().execute(
            CreateTaskCommand(
                actor_id=current_user_id(request),
                title=data["title"],
                description=data["description"],
                due_date=data["due_date"],
                assignee_id=data["assignee"],
            )
        )
        return Response(_serialize(task), status=status.HTTP_201_CREATED)


class TaskDetailView(APIView):
    def get(self, request: Request, task_id: int) -> Response:
        return Response(_serialize(container.get_task().execute(task_id)))

    def patch(self, request: Request, task_id: int) -> Response:
        payload = TaskUpdateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        task = container.update_task().execute(
            UpdateTaskCommand(
                actor_id=current_user_id(request),
                task_id=task_id,
                changes=_task_changes(data),
                expected_version=data.get("version"),
            )
        )
        return Response(_serialize(task))

    def delete(self, request: Request, task_id: int) -> Response:
        container.delete_task().execute(actor_id=current_user_id(request), task_id=task_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


# API field name -> TaskChanges attribute. Only fields present in the request are changed.
_CHANGEABLE_FIELDS = {
    "title": "title",
    "description": "description",
    "status": "status",
    "due_date": "due_date",
    "assignee": "assignee_id",
}


def _task_changes(data: dict[str, Any]) -> TaskChanges:
    changes = {
        attribute: data[field] for field, attribute in _CHANGEABLE_FIELDS.items() if field in data
    }
    if "status" in changes:
        changes["status"] = TaskStatus(changes["status"])
    return TaskChanges(**changes)


def _task_filter(params: dict[str, Any], user_id: int) -> TaskFilter:
    status_value = params.get("status")
    return TaskFilter(
        status=TaskStatus(status_value) if status_value else None,
        due_after=params.get("due_after"),
        due_before=params.get("due_before"),
        assignee_id=_assignee_id(params.get("assignee"), user_id),
        overdue=params["overdue"],
    )


def _assignee_id(value: str | None, user_id: int) -> int | None:
    if value is None:
        return None
    if value == "me":
        return user_id
    return int(value)


def _serialize(task: Task) -> dict[str, Any]:
    return dict(TaskSerializer(task, context={"today": container.today()}).data)
