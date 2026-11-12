from datetime import UTC, datetime
from typing import Any

from factory.declarations import LazyAttribute, LazyFunction, Sequence
from factory.django import DjangoModelFactory

from apps.tasks.domain.task import TaskStatus
from apps.tasks.infrastructure import models
from apps.users.tests.factories import make_user

CREATED_AT = datetime(2026, 11, 1, 9, 0, tzinfo=UTC)
COMPLETED_AT = datetime(2026, 11, 5, 17, 0, tzinfo=UTC)


class _TaskFactory(DjangoModelFactory[models.Task]):
    class Meta:
        model = models.Task

    title = Sequence(lambda n: f"Task {n}")
    status = TaskStatus.TODO.value
    created_by = LazyFunction(make_user)
    # Keeps rows valid against the "completed_at matches status" constraint.
    completed_at = LazyAttribute(lambda row: COMPLETED_AT if row.status == "done" else None)
    created_at = CREATED_AT
    updated_at = CREATED_AT


def make_task_row(**fields: Any) -> models.Task:
    """Writes a row directly, bypassing the repository (for constraint and query tests)."""
    return _TaskFactory.create(**fields)
