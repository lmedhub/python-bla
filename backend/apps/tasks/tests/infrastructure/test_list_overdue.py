from datetime import UTC, date, datetime, timedelta

import pytest

from apps.tasks.domain.task import TaskStatus
from apps.tasks.infrastructure.repositories import DjangoTaskRepository
from apps.tasks.tests.factories import make_task_row
from apps.tasks.tests.fakes import FixedClock

pytestmark = pytest.mark.django_db

TODAY = date(2026, 11, 12)
YESTERDAY = TODAY - timedelta(days=1)
LAST_WEEK = TODAY - timedelta(days=7)


@pytest.fixture
def repository() -> DjangoTaskRepository:
    return DjangoTaskRepository(clock=FixedClock(datetime(2026, 11, 12, 9, 0, tzinfo=UTC)))


def test_lists_unfinished_tasks_due_before_today_oldest_first(repository):
    yesterday = make_task_row(due_date=YESTERDAY, status=TaskStatus.IN_PROGRESS.value)
    last_week = make_task_row(due_date=LAST_WEEK)
    unassigned = make_task_row(due_date=YESTERDAY, assignee=None)

    overdue = repository.list_overdue(TODAY)

    assert [task.id for task in overdue] == [last_week.pk, yesterday.pk, unassigned.pk]


def test_leaves_out_tasks_that_are_not_overdue(repository):
    make_task_row(due_date=TODAY)
    make_task_row(due_date=None)
    make_task_row(due_date=YESTERDAY, status=TaskStatus.DONE.value)

    assert repository.list_overdue(TODAY) == []


def test_uses_one_query(repository, django_assert_num_queries):
    for _ in range(3):
        make_task_row(due_date=YESTERDAY)

    with django_assert_num_queries(1):
        repository.list_overdue(TODAY)
