from dataclasses import dataclass
from datetime import date
from enum import Enum

from apps.tasks.application.ports import Clock, Notifier, TaskRepository, UserDirectory
from apps.tasks.application.queries import Page, PageRequest, TaskFilter
from apps.tasks.domain.task import Task, TaskStatus


class Unset(Enum):
    """Marks a PATCH field that was not sent, which is different from one sent as null."""

    UNSET = "unset"


UNSET = Unset.UNSET


@dataclass(frozen=True)
class CreateTaskCommand:
    actor_id: int
    title: str
    description: str = ""
    due_date: date | None = None
    assignee_id: int | None = None


@dataclass(frozen=True)
class TaskChanges:
    title: str | Unset = UNSET
    description: str | Unset = UNSET
    status: TaskStatus | Unset = UNSET
    due_date: date | Unset | None = UNSET
    assignee_id: int | Unset | None = UNSET


@dataclass(frozen=True)
class UpdateTaskCommand:
    actor_id: int
    task_id: int
    changes: TaskChanges


class CreateTask:
    def __init__(
        self, tasks: TaskRepository, users: UserDirectory, notifier: Notifier, clock: Clock
    ) -> None:
        self._tasks = tasks
        self._users = users
        self._notifier = notifier
        self._clock = clock

    def execute(self, command: CreateTaskCommand) -> Task:
        raise NotImplementedError


class GetTask:
    def __init__(self, tasks: TaskRepository) -> None:
        self._tasks = tasks

    def execute(self, task_id: int) -> Task:
        raise NotImplementedError


class ListTasks:
    def __init__(self, tasks: TaskRepository, clock: Clock) -> None:
        self._tasks = tasks
        self._clock = clock

    def execute(self, task_filter: TaskFilter, page: PageRequest) -> Page[Task]:
        raise NotImplementedError


class UpdateTask:
    def __init__(
        self, tasks: TaskRepository, users: UserDirectory, notifier: Notifier, clock: Clock
    ) -> None:
        self._tasks = tasks
        self._users = users
        self._notifier = notifier
        self._clock = clock

    def execute(self, command: UpdateTaskCommand) -> Task:
        raise NotImplementedError


class DeleteTask:
    def __init__(self, tasks: TaskRepository) -> None:
        self._tasks = tasks

    def execute(self, actor_id: int, task_id: int) -> None:
        raise NotImplementedError
