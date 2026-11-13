"""HTTP in, use case call, HTTP out. No business rules and no ORM here."""

from datetime import tzinfo
from typing import Any

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.interfaces.requests import current_user_id, request_time_zone
from apps.core.interfaces.schema import TIME_ZONE_PARAMETER, error_responses
from apps.tasks.application.queries import PageRequest, TaskFilter
from apps.tasks.application.use_cases import CreateTaskCommand, TaskChanges, UpdateTaskCommand
from apps.tasks.domain.task import Task, TaskStatus
from apps.tasks.interfaces import container
from apps.tasks.interfaces.pagination import paginated
from apps.tasks.interfaces.serializers import (
    PaginatedTaskListSerializer,
    TaskCreateSerializer,
    TaskListQuerySerializer,
    TaskSerializer,
    TaskUpdateSerializer,
)


class TaskCollectionView(APIView):
    @extend_schema(
        operation_id="tasks_list",
        summary="List tasks",
        description="Ordered by due date (no date last), then id. Filters combine with AND.",
        parameters=[TaskListQuerySerializer, TIME_ZONE_PARAMETER],
        responses={200: PaginatedTaskListSerializer, **error_responses(400, 401, 429)},
    )
    def get(self, request: Request) -> Response:
        query = TaskListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data

        zone = request_time_zone(request)
        page = container.list_tasks(zone).execute(
            _task_filter(params, current_user_id(request)),
            PageRequest(page=params["page"], page_size=params["page_size"]),
        )
        results = [_serialize(task, zone) for task in page.items]
        return Response(paginated(request, page, results))

    @extend_schema(
        summary="Create a task",
        description="The caller becomes the creator. The due date may not be in the past.",
        parameters=[TIME_ZONE_PARAMETER],
        request=TaskCreateSerializer,
        responses={201: TaskSerializer, **error_responses(400, 401, 429)},
    )
    def post(self, request: Request) -> Response:
        payload = TaskCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        zone = request_time_zone(request)
        task = container.create_task(zone).execute(
            CreateTaskCommand(
                actor_id=current_user_id(request),
                title=data["title"],
                description=data["description"],
                due_date=data["due_date"],
                assignee_id=data["assignee"],
            )
        )
        return Response(_serialize(task, zone), status=status.HTTP_201_CREATED)


class TaskDetailView(APIView):
    @extend_schema(
        summary="Get a task",
        parameters=[TIME_ZONE_PARAMETER],
        responses={200: TaskSerializer, **error_responses(400, 401, 404, 429)},
    )
    def get(self, request: Request, task_id: int) -> Response:
        task = container.get_task().execute(task_id)
        return Response(_serialize(task, request_time_zone(request)))

    @extend_schema(
        summary="Change a task",
        description="Only the fields sent change. The creator may change anything; the "
        "assignee only the status. Send `version` to get a 409 instead of overwriting a "
        "newer change.",
        parameters=[TIME_ZONE_PARAMETER],
        request=TaskUpdateSerializer,
        responses={200: TaskSerializer, **error_responses(400, 401, 403, 404, 409, 429)},
    )
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
        return Response(_serialize(task, request_time_zone(request)))

    @extend_schema(
        summary="Delete a task",
        description="Only the creator may delete.",
        responses={
            204: OpenApiResponse(description="Deleted."),
            **error_responses(401, 403, 404, 429),
        },
    )
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


def _serialize(task: Task, zone: tzinfo) -> dict[str, Any]:
    return dict(TaskSerializer(task, context={"today": container.today(zone)}).data)
