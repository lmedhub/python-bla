import pytest

from apps.core.domain.errors import ConflictError, PermissionDeniedError
from apps.tasks.application.use_cases import TaskChanges, UpdateTask, UpdateTaskCommand
from apps.tasks.domain.task import Task, TaskStatus
from apps.tasks.tests.application.constants import ASSIGNEE, CREATOR, STRANGER
from apps.tasks.tests.fakes import InMemoryTaskRepository


@pytest.fixture
def update_task(tasks, users, notifier, clock) -> UpdateTask:
    return UpdateTask(tasks=tasks, users=users, notifier=notifier, clock=clock)


@pytest.fixture
def task(tasks: InMemoryTaskRepository) -> Task:
    return tasks.add(Task(title="Write tests", created_by_id=CREATOR, assignee_id=ASSIGNEE))


def rename(task: Task, actor_id: int, expected_version: int | None) -> UpdateTaskCommand:
    return UpdateTaskCommand(
        actor_id=actor_id,
        task_id=task.require_id(),
        changes=TaskChanges(title="Renamed"),
        expected_version=expected_version,
    )


def test_new_tasks_start_at_version_one(task):
    assert task.version == 1


def test_each_update_increments_the_version(update_task, task):
    first = update_task.execute(rename(task, CREATOR, expected_version=None))
    second = update_task.execute(
        UpdateTaskCommand(
            actor_id=ASSIGNEE,
            task_id=task.require_id(),
            changes=TaskChanges(status=TaskStatus.DONE),
        )
    )

    assert (first.version, second.version) == (2, 3)


def test_matching_expected_version_is_accepted(update_task, task):
    updated = update_task.execute(rename(task, CREATOR, expected_version=1))

    assert updated.title == "Renamed"


def test_stale_expected_version_is_a_conflict_and_nothing_is_saved(update_task, task, tasks):
    update_task.execute(rename(task, CREATOR, expected_version=1))  # someone else saved first

    with pytest.raises(ConflictError):
        update_task.execute(
            UpdateTaskCommand(
                actor_id=CREATOR,
                task_id=task.require_id(),
                changes=TaskChanges(title="My stale edit"),
                expected_version=1,
            )
        )

    assert tasks.get(task.require_id()).title == "Renamed"


def test_permission_is_checked_before_the_version(update_task, task):
    with pytest.raises(PermissionDeniedError):
        update_task.execute(rename(task, STRANGER, expected_version=42))
