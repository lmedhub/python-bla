"""What the use cases need from the outside world. Infrastructure provides the real ones."""

from collections.abc import Collection
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from apps.tasks.application.queries import Page, PageRequest, TaskFilter
from apps.tasks.domain.task import Task


class Clock(Protocol):
    def now(self) -> datetime: ...

    def today(self) -> date: ...


class TaskRepository(Protocol):
    def get(self, task_id: int) -> Task | None: ...

    def add(self, task: Task) -> Task: ...

    def update(self, task: Task) -> Task:
        """Save only if the stored version still equals `task.version`, else raise ConflictError.

        Returns the task with `version + 1`.
        """
        ...

    def delete(self, task_id: int) -> None: ...

    def find(self, task_filter: TaskFilter, page: PageRequest, today: date) -> Page[Task]: ...

    def list_overdue(self, today: date) -> list[Task]:
        """Every overdue task, assigned or not, ordered by due date then id. Not paginated."""
        ...


@dataclass(frozen=True)
class Recipient:
    email: str
    name: str


class UserDirectory(Protocol):
    def is_active_user(self, user_id: int) -> bool: ...

    def active_recipients(self, user_ids: Collection[int]) -> dict[int, Recipient]:
        """Contact details of the active users among `user_ids`; others are left out."""
        ...


class Notifier(Protocol):
    """Called inside the request. Must be quick and must not fail the request."""

    def task_assigned(self, task_id: int, assignee_id: int) -> None: ...


class Mailer(Protocol):
    def send(self, *, to: str, subject: str, body: str) -> None: ...


class SentLog(Protocol):
    """Remembers which emails went out, so a retried or repeated job does not resend them."""

    def was_sent(self, key: str) -> bool: ...

    def record(self, key: str) -> None: ...
