from dataclasses import replace
from datetime import date
from typing import Any

from django.db.models import F, Q

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
        rows = models.Task.objects.filter(_conditions(task_filter, today)).order_by(
            # Tasks without a due date go last; id breaks ties so pages never overlap.
            F("due_date").asc(nulls_last=True),
            "id",
        )
        total = rows.count()
        items = [_to_entity(row) for row in rows[page.offset : page.offset + page.page_size]]
        return Page(items=items, total=total, request=page)


def _conditions(task_filter: TaskFilter, today: date) -> Q:
    condition = Q()
    if task_filter.status is not None:
        condition &= Q(status=task_filter.status.value)
    if task_filter.assignee_id is not None:
        condition &= Q(assignee_id=task_filter.assignee_id)
    if task_filter.due_after is not None:
        condition &= Q(due_date__gte=task_filter.due_after)
    if task_filter.due_before is not None:
        condition &= Q(due_date__lte=task_filter.due_before)
    if task_filter.overdue is not None:
        # Same rule as Task.is_overdue. Django's negation keeps tasks with no due date.
        overdue = Q(due_date__lt=today) & ~Q(status=TaskStatus.DONE.value)
        condition &= overdue if task_filter.overdue else ~overdue
    return condition


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
