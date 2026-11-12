"""What the use cases need from the outside world. Infrastructure provides the real ones."""

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


class UserDirectory(Protocol):
    def is_active_user(self, user_id: int) -> bool: ...


class Notifier(Protocol):
    def task_assigned(self, task_id: int, assignee_id: int) -> None: ...
