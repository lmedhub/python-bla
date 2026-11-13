"""Serializers check types and shapes. Business rules (blank title, past due date, who may
change what) live in the domain, so an unauthorised caller gets 403 before any rule is
revealed (ADR 0008)."""

from typing import Any

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.tasks.application.queries import DEFAULT_PAGE_SIZE
from apps.tasks.domain.task import Task, TaskStatus

STATUS_CHOICES = [status.value for status in TaskStatus]


class TaskSerializer(serializers.Serializer[Task]):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    status = serializers.ChoiceField(choices=STATUS_CHOICES, read_only=True)
    due_date = serializers.DateField(read_only=True, allow_null=True)
    created_by = serializers.IntegerField(source="created_by_id", read_only=True)
    assignee = serializers.IntegerField(source="assignee_id", read_only=True, allow_null=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    version = serializers.IntegerField(read_only=True)
    is_overdue = serializers.SerializerMethodField()

    @extend_schema_field(serializers.BooleanField())
    def get_is_overdue(self, task: Task) -> bool:
        # The server's clock decides, so every client agrees on what "overdue" means.
        return task.is_overdue(today=self.context["today"])


class TaskCreateSerializer(serializers.Serializer[Any]):
    title = serializers.CharField(allow_blank=True, trim_whitespace=False)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    due_date = serializers.DateField(required=False, allow_null=True, default=None)
    assignee = serializers.IntegerField(required=False, allow_null=True, default=None)


class TaskUpdateSerializer(serializers.Serializer[Any]):
    """PATCH: every field is optional, and only the fields sent are changed."""

    title = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=STATUS_CHOICES, required=False)
    due_date = serializers.DateField(required=False, allow_null=True)
    assignee = serializers.IntegerField(required=False, allow_null=True)
    version = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="The version you last read. If the task changed since, the update is a 409.",
    )


class TaskListQuerySerializer(serializers.Serializer[Any]):
    status = serializers.ChoiceField(choices=STATUS_CHOICES, required=False)
    due_after = serializers.DateField(required=False, help_text="Inclusive.")
    due_before = serializers.DateField(required=False, help_text="Inclusive.")
    assignee = serializers.CharField(required=False, help_text='A user id, or "me".')
    # For query strings DRF reads a missing boolean as False; default=None keeps "not sent".
    overdue = serializers.BooleanField(required=False, allow_null=True, default=None)
    page = serializers.IntegerField(required=False, default=1)
    page_size = serializers.IntegerField(required=False, default=DEFAULT_PAGE_SIZE)

    def validate_assignee(self, value: str) -> str:
        if value == "me" or (value.isdigit() and int(value) > 0):
            return value
        raise serializers.ValidationError('Must be a user id or "me".')


class PaginatedTaskListSerializer(serializers.Serializer[Any]):
    """Documents the list envelope. Links are relative, so they work behind any proxy."""

    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = TaskSerializer(many=True)
