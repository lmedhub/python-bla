from dataclasses import replace
from datetime import date
from typing import Any

from django.db.models import F

from apps.core.domain.errors import ConflictError
from apps.tasks.application.ports import Clock
from apps.tasks.application.queries import Page, PageRequest, TaskFilter
from apps.tasks.domain.task import Task, TaskStatus
from apps.tasks.infrastructure import models


class DjangoTaskRepository:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def get(self, task_id: int) -> Task | None:
        row = models.Task.objects.filter(pk=task_id).first()
        return _to_entity(row) if row else None

    def add(self, task: Task) -> Task:
        now = self._clock.now()
        row = models.Task.objects.create(**_columns(task), created_at=now, updated_at=now)
        return _to_entity(row)

    def update(self, task: Task) -> Task:
        now = self._clock.now()
        # Optimistic locking in one statement: the WHERE on version makes a concurrent
        # writer's UPDATE match zero rows instead of overwriting the first write.
        matched = models.Task.objects.filter(pk=task.require_id(), version=task.version).update(
            **_columns(task), version=F("version") + 1, updated_at=now
        )
        if matched == 0:
            raise ConflictError("Task was changed or deleted by someone else.")
        return replace(task, version=task.version + 1, updated_at=now)

    def delete(self, task_id: int) -> None:
        models.Task.objects.filter(pk=task_id).delete()

    def find(self, task_filter: TaskFilter, page: PageRequest, today: date) -> Page[Task]:
        raise NotImplementedError


def _columns(task: Task) -> dict[str, Any]:
    """The writable columns. id, version and timestamps are managed by the repository."""
    return {
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "due_date": task.due_date,
        "created_by_id": task.created_by_id,
        "assignee_id": task.assignee_id,
        "completed_at": task.completed_at,
    }


def _to_entity(row: models.Task) -> Task:
    return Task(
        id=row.pk,
        title=row.title,
        description=row.description,
        status=TaskStatus(row.status),
        due_date=row.due_date,
        created_by_id=row.created_by_id,
        assignee_id=row.assignee_id,
        completed_at=row.completed_at,
        version=row.version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
