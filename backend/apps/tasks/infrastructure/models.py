from typing import ClassVar

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.tasks.domain.rules import TITLE_MAX_LENGTH
from apps.tasks.domain.task import TaskStatus


class Task(models.Model):
    title = models.CharField(max_length=TITLE_MAX_LENGTH)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.value) for status in TaskStatus],
        default=TaskStatus.TODO.value,
    )
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    # Set from the Clock port by the repository, not auto_now, so tests control time.
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        indexes: ClassVar[list[models.Index]] = [
            # Serves the default list order and the status / due date filters.
            models.Index(fields=["status", "due_date"], name="tasks_status_due_date_idx"),
        ]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            # A string column with a check, not a database enum: adding a status is a
            # one-line migration instead of an ALTER TYPE.
            models.CheckConstraint(
                condition=Q(status__in=[status.value for status in TaskStatus]),
                name="tasks_task_status_valid",
            ),
            models.CheckConstraint(condition=~Q(title=""), name="tasks_task_title_not_blank"),
            # Mirrors Task.change_status: completed_at is set exactly when the task is done.
            models.CheckConstraint(
                condition=(
                    Q(status=TaskStatus.DONE.value, completed_at__isnull=False)
                    | (~Q(status=TaskStatus.DONE.value) & Q(completed_at__isnull=True))
                ),
                name="tasks_task_completed_at_matches_status",
            ),
        ]

    def __str__(self) -> str:
        return self.title


class SentNotification(models.Model):
    """One row per email sent by a job. The unique key is what makes the jobs idempotent."""

    key = models.CharField(max_length=200, unique=True)
    sent_at = models.DateTimeField()

    def __str__(self) -> str:
        return self.key
