from datetime import timedelta

import pytest

from apps.core.domain.errors import InvalidInputError
from apps.tasks.application.use_cases import CreateTask, CreateTaskCommand
from apps.tasks.domain.task import TaskStatus
from apps.tasks.tests.application.constants import (
    ASSIGNEE,
    CREATOR,
    INACTIVE_USER,
    NOW,
    UNKNOWN_USER,
)

TODAY = NOW.date()


@pytest.fixture
def create_task(tasks, users, notifier, clock) -> CreateTask:
    return CreateTask(tasks=tasks, users=users, notifier=notifier, clock=clock)


def command(**overrides) -> CreateTaskCommand:
    return CreateTaskCommand(**{"actor_id": CREATOR, "title": "Write tests", **overrides})


def test_creates_a_todo_task_owned_by_the_actor(create_task, tasks):
    task = create_task.execute(command(description="Cover the rules", due_date=TODAY))

    assert task.id is not None
    assert task.created_by_id == CREATOR
    assert task.status is TaskStatus.TODO
    assert task.description == "Cover the rules"
    assert tasks.get(task.id) == task


def test_trims_the_title(create_task):
    task = create_task.execute(command(title="  Write tests  "))

    assert task.title == "Write tests"


def test_rejects_a_blank_title_and_saves_nothing(create_task, tasks):
    with pytest.raises(InvalidInputError) as error:
        create_task.execute(command(title="   "))

    assert list(error.value.fields) == ["title"]
    assert tasks.rows == {}


def test_rejects_a_due_date_in_the_past(create_task):
    with pytest.raises(InvalidInputError) as error:
        create_task.execute(command(due_date=TODAY - timedelta(days=1)))

    assert list(error.value.fields) == ["due_date"]


@pytest.mark.parametrize("assignee_id", [UNKNOWN_USER, INACTIVE_USER])
def test_rejects_an_unknown_or_inactive_assignee_as_invalid_input(create_task, assignee_id):
    with pytest.raises(InvalidInputError) as error:
        create_task.execute(command(assignee_id=assignee_id))

    assert list(error.value.fields) == ["assignee"]


def test_notifies_the_assignee(create_task, notifier):
    task = create_task.execute(command(assignee_id=ASSIGNEE))

    assert notifier.assignments == [(task.id, ASSIGNEE)]


def test_does_not_notify_when_unassigned(create_task, notifier):
    create_task.execute(command())

    assert notifier.assignments == []
