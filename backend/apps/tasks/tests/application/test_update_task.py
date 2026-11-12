from datetime import timedelta

import pytest

from apps.core.domain.errors import InvalidInputError, NotFoundError, PermissionDeniedError
from apps.tasks.application.use_cases import TaskChanges, UpdateTask, UpdateTaskCommand
from apps.tasks.domain.task import Task, TaskStatus
from apps.tasks.tests.application.constants import (
    ASSIGNEE,
    CREATOR,
    INACTIVE_USER,
    NOW,
    STRANGER,
    UNKNOWN_USER,
)
from apps.tasks.tests.fakes import InMemoryTaskRepository

TODAY = NOW.date()


@pytest.fixture
def update_task(tasks, users, notifier, clock) -> UpdateTask:
    return UpdateTask(tasks=tasks, users=users, notifier=notifier, clock=clock)


@pytest.fixture
def task(tasks: InMemoryTaskRepository) -> Task:
    return tasks.add(
        Task(title="Write tests", created_by_id=CREATOR, assignee_id=ASSIGNEE, due_date=TODAY)
    )


def run(update_task: UpdateTask, task: Task, actor_id: int, **changes) -> Task:
    return update_task.execute(
        UpdateTaskCommand(
            actor_id=actor_id, task_id=task.require_id(), changes=TaskChanges(**changes)
        )
    )


def test_unknown_task_is_not_found(update_task):
    command = UpdateTaskCommand(actor_id=CREATOR, task_id=999, changes=TaskChanges())

    with pytest.raises(NotFoundError):
        update_task.execute(command)


class TestCreator:
    def test_can_edit_the_title_and_it_is_saved(self, update_task, task, tasks):
        updated = run(update_task, task, CREATOR, title="  Write more tests ")

        assert updated.title == "Write more tests"
        assert tasks.get(task.require_id()).title == "Write more tests"

    def test_can_set_a_past_due_date_on_update(self, update_task, task):
        updated = run(update_task, task, CREATOR, due_date=TODAY - timedelta(days=3))

        assert updated.due_date == TODAY - timedelta(days=3)

    def test_can_clear_optional_fields(self, update_task, task):
        updated = run(update_task, task, CREATOR, due_date=None, assignee_id=None)

        assert updated.due_date is None
        assert updated.assignee_id is None

    def test_fields_that_are_not_sent_stay_unchanged(self, update_task, task):
        updated = run(update_task, task, CREATOR, description="More detail")

        assert updated.title == "Write tests"
        assert updated.assignee_id == ASSIGNEE
        assert updated.due_date == TODAY

    def test_blank_title_is_invalid(self, update_task, task):
        with pytest.raises(InvalidInputError) as error:
            run(update_task, task, CREATOR, title=" ")

        assert list(error.value.fields) == ["title"]


class TestAssignee:
    def test_can_complete_the_task_with_the_time_from_the_clock(self, update_task, task):
        updated = run(update_task, task, ASSIGNEE, status=TaskStatus.DONE)

        assert updated.status is TaskStatus.DONE
        assert updated.completed_at == NOW

    def test_completing_twice_keeps_the_first_completion_time(self, update_task, task, clock):
        run(update_task, task, ASSIGNEE, status=TaskStatus.DONE)
        clock.advance(timedelta(hours=2))

        updated = run(update_task, task, ASSIGNEE, status=TaskStatus.DONE)

        assert updated.completed_at == NOW

    def test_cannot_change_the_title_and_nothing_is_saved(self, update_task, task, tasks):
        with pytest.raises(PermissionDeniedError):
            run(update_task, task, ASSIGNEE, status=TaskStatus.DONE, title="Mine now")

        stored = tasks.get(task.require_id())
        assert stored.title == "Write tests"
        assert stored.status is TaskStatus.TODO

    def test_may_resend_unchanged_fields_with_a_status_change(self, update_task, task):
        updated = run(
            update_task, task, ASSIGNEE, status=TaskStatus.IN_PROGRESS, title="Write tests"
        )

        assert updated.status is TaskStatus.IN_PROGRESS


class TestStranger:
    def test_cannot_change_the_status(self, update_task, task):
        with pytest.raises(PermissionDeniedError):
            run(update_task, task, STRANGER, status=TaskStatus.DONE)

    def test_gets_permission_denied_before_validation(self, update_task, task):
        # A blank title must not reveal validation details to someone who may not edit.
        with pytest.raises(PermissionDeniedError):
            run(update_task, task, STRANGER, title="  ")


class TestReassignment:
    def test_notifies_the_new_assignee(self, update_task, task, notifier):
        run(update_task, task, CREATOR, assignee_id=CREATOR)

        assert notifier.assignments == [(task.id, CREATOR)]

    def test_keeping_the_same_assignee_does_not_notify(self, update_task, task, notifier):
        run(update_task, task, CREATOR, assignee_id=ASSIGNEE, title="Renamed")

        assert notifier.assignments == []

    def test_unassigning_does_not_notify(self, update_task, task, notifier):
        run(update_task, task, CREATOR, assignee_id=None)

        assert notifier.assignments == []

    @pytest.mark.parametrize("assignee_id", [UNKNOWN_USER, INACTIVE_USER])
    def test_rejects_an_unknown_or_inactive_assignee(
        self, update_task, task, notifier, assignee_id
    ):
        with pytest.raises(InvalidInputError) as error:
            run(update_task, task, CREATOR, assignee_id=assignee_id)

        assert list(error.value.fields) == ["assignee"]
        assert notifier.assignments == []
