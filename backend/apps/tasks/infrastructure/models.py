from django.conf import settings
from django.db import models

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
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    def __str__(self) -> str:
        return self.title
