from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest

from apps.tasks.domain.task import Task, TaskStatus

CREATOR = 1
ASSIGNEE = 2
STRANGER = 3

NOW = datetime(2026, 11, 12, 9, 30, tzinfo=UTC)
TODAY = NOW.date()


def make_task(**overrides: Any) -> Task:
    return Task(**{"title": "Write tests", "created_by_id": CREATOR, **overrides})


class TestNewTask:
    def test_starts_as_todo_with_no_completion_time(self):
        task = make_task()

        assert task.status is TaskStatus.TODO
        assert task.completed_at is None
        assert task.description == ""
        assert task.id is None


class TestChangeStatus:
    def test_completing_sets_completed_at(self):
        task = make_task()

        task.change_status(TaskStatus.DONE, now=NOW)

        assert task.status is TaskStatus.DONE
        assert task.completed_at == NOW

    def test_completing_again_keeps_the_first_completion_time(self):
        task = make_task()
        task.change_status(TaskStatus.DONE, now=NOW)

        task.change_status(TaskStatus.DONE, now=NOW + timedelta(hours=1))

        assert task.completed_at == NOW

    def test_reopening_clears_completed_at(self):
        task = make_task()
        task.change_status(TaskStatus.DONE, now=NOW)

        task.change_status(TaskStatus.IN_PROGRESS, now=NOW)

        assert task.status is TaskStatus.IN_PROGRESS
        assert task.completed_at is None

    def test_starting_work_does_not_set_completed_at(self):
        task = make_task()

        task.change_status(TaskStatus.IN_PROGRESS, now=NOW)

        assert task.completed_at is None


class TestOverdue:
    @pytest.mark.parametrize(
        ("due_date", "status", "expected"),
        [
            (TODAY - timedelta(days=1), TaskStatus.TODO, True),
            (TODAY - timedelta(days=1), TaskStatus.IN_PROGRESS, True),
            (TODAY, TaskStatus.TODO, False),
            (TODAY + timedelta(days=1), TaskStatus.TODO, False),
            (TODAY - timedelta(days=1), TaskStatus.DONE, False),
            (None, TaskStatus.TODO, False),
        ],
    )
    def test_overdue_means_past_due_and_not_done(
        self, due_date: date | None, status: TaskStatus, expected: bool
    ):
        task = make_task(due_date=due_date, status=status)

        assert task.is_overdue(today=TODAY) is expected


class TestPermissions:
    def test_creator_can_change_any_field(self):
        task = make_task(assignee_id=ASSIGNEE)

        assert task.can_be_updated_by(CREATOR, {"title", "assignee_id", "status"})

    def test_assignee_can_change_status(self):
        task = make_task(assignee_id=ASSIGNEE)

        assert task.can_be_updated_by(ASSIGNEE, {"status"})

    def test_assignee_cannot_change_other_fields(self):
        task = make_task(assignee_id=ASSIGNEE)

        assert not task.can_be_updated_by(ASSIGNEE, {"status", "title"})

    def test_anyone_else_cannot_change_anything(self):
        task = make_task(assignee_id=ASSIGNEE)

        assert not task.can_be_updated_by(STRANGER, {"status"})

    def test_only_the_creator_can_delete(self):
        task = make_task(assignee_id=ASSIGNEE)

        assert task.can_be_deleted_by(CREATOR)
        assert not task.can_be_deleted_by(ASSIGNEE)
        assert not task.can_be_deleted_by(STRANGER)


class TestRequireId:
    def test_returns_the_id_of_a_saved_task(self):
        assert make_task(id=7).require_id() == 7

    def test_fails_loudly_for_an_unsaved_task(self):
        with pytest.raises(RuntimeError, match="not been saved"):
            make_task().require_id()
