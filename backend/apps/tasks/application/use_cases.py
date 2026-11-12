from dataclasses import dataclass, fields
from datetime import date
from enum import Enum

from apps.core.domain.errors import InvalidInputError, NotFoundError, PermissionDeniedError
from apps.tasks.application.ports import Clock, Notifier, TaskRepository, UserDirectory
from apps.tasks.application.queries import Page, PageRequest, TaskFilter
from apps.tasks.domain.rules import check_due_date_on_create, clean_title
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
    """Field names match Task attributes, so changed fields can be found generically."""

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
        title = clean_title(command.title)
        check_due_date_on_create(command.due_date, today=self._clock.today())
        if command.assignee_id is not None:
            _check_assignee(self._users, command.assignee_id)

        task = self._tasks.add(
            Task(
                title=title,
                description=command.description,
                created_by_id=command.actor_id,
                due_date=command.due_date,
                assignee_id=command.assignee_id,
            )
        )
        if task.assignee_id is not None:
            self._notifier.task_assigned(task.require_id(), task.assignee_id)
        return task


class GetTask:
    def __init__(self, tasks: TaskRepository) -> None:
        self._tasks = tasks

    def execute(self, task_id: int) -> Task:
        return _get_existing(self._tasks, task_id)


class ListTasks:
    def __init__(self, tasks: TaskRepository, clock: Clock) -> None:
        self._tasks = tasks
        self._clock = clock

    def execute(self, task_filter: TaskFilter, page: PageRequest) -> Page[Task]:
        # "Overdue" depends on today's date, which only the clock knows.
        return self._tasks.find(task_filter, page, today=self._clock.today())


class UpdateTask:
    def __init__(
        self, tasks: TaskRepository, users: UserDirectory, notifier: Notifier, clock: Clock
    ) -> None:
        self._tasks = tasks
        self._users = users
        self._notifier = notifier
        self._clock = clock

    def execute(self, command: UpdateTaskCommand) -> Task:
        task = _get_existing(self._tasks, command.task_id)
        changes = command.changes

        # Permission comes first, so someone who may not edit learns nothing from validation.
        if not task.can_be_updated_by(command.actor_id, _changed_fields(task, changes)):
            raise PermissionDeniedError("You may not change these fields of this task.")

        previous_assignee_id = task.assignee_id
        if not isinstance(changes.title, Unset):
            task.title = clean_title(changes.title)
        if not isinstance(changes.description, Unset):
            task.description = changes.description
        if not isinstance(changes.due_date, Unset):
            task.due_date = changes.due_date
        if not isinstance(changes.assignee_id, Unset):
            new_assignee_id = changes.assignee_id
            if new_assignee_id is not None and new_assignee_id != previous_assignee_id:
                _check_assignee(self._users, new_assignee_id)
            task.assignee_id = new_assignee_id
        if not isinstance(changes.status, Unset):
            task.change_status(changes.status, now=self._clock.now())

        saved = self._tasks.update(task)
        if saved.assignee_id is not None and saved.assignee_id != previous_assignee_id:
            self._notifier.task_assigned(saved.require_id(), saved.assignee_id)
        return saved


class DeleteTask:
    def __init__(self, tasks: TaskRepository) -> None:
        self._tasks = tasks

    def execute(self, actor_id: int, task_id: int) -> None:
        task = _get_existing(self._tasks, task_id)
        if not task.can_be_deleted_by(actor_id):
            raise PermissionDeniedError("Only the creator may delete this task.")
        self._tasks.delete(task_id)


def _get_existing(tasks: TaskRepository, task_id: int) -> Task:
    task = tasks.get(task_id)
    if task is None:
        raise NotFoundError("Task not found.")
    return task


def _check_assignee(users: UserDirectory, assignee_id: int) -> None:
    # A bad assignee is a validation error on that field (400), not a conflict (409).
    if not users.is_active_user(assignee_id):
        raise InvalidInputError.on("assignee", "Must be an active user.")


def _changed_fields(task: Task, changes: TaskChanges) -> set[str]:
    """Fields that were sent and differ from the task. Re-sending a value is not a change."""
    changed = set()
    for field in fields(changes):
        value = getattr(changes, field.name)
        if value is UNSET:
            continue
        if field.name == "title" and isinstance(value, str):
            value = value.strip()  # compare the way the title is stored
        if getattr(task, field.name) != value:
            changed.add(field.name)
    return changed
