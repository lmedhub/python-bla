from datetime import UTC, date, datetime, timedelta

import pytest

from apps.tasks.application.queries import PageRequest, TaskFilter
from apps.tasks.domain.task import Task, TaskStatus
from apps.tasks.infrastructure.repositories import DjangoTaskRepository
from apps.tasks.tests.factories import make_task_row
from apps.tasks.tests.fakes import FixedClock
from apps.users.tests.factories import make_user

pytestmark = pytest.mark.django_db

TODAY = date(2026, 11, 12)
YESTERDAY = TODAY - timedelta(days=1)
TOMORROW = TODAY + timedelta(days=1)
ALL = PageRequest(page=1, page_size=100)


@pytest.fixture
def repository() -> DjangoTaskRepository:
    return DjangoTaskRepository(clock=FixedClock(datetime(2026, 11, 12, 9, 0, tzinfo=UTC)))


def ids(repository: DjangoTaskRepository, task_filter: TaskFilter, page: PageRequest = ALL):
    return [task.id for task in repository.find(task_filter, page, today=TODAY).items]


def test_returns_domain_tasks(repository):
    make_task_row()

    page = repository.find(TaskFilter(), ALL, today=TODAY)

    assert page.total == 1
    assert isinstance(page.items[0], Task)


def test_sorts_by_due_date_with_no_due_date_last_then_by_id(repository):
    no_date_1 = make_task_row(due_date=None)
    later = make_task_row(due_date=TOMORROW)
    earlier = make_task_row(due_date=YESTERDAY)
    no_date_2 = make_task_row(due_date=None)
    same_day = make_task_row(due_date=YESTERDAY)

    assert ids(repository, TaskFilter()) == [
        earlier.pk,
        same_day.pk,
        later.pk,
        no_date_1.pk,
        no_date_2.pk,
    ]


def test_filters_by_status(repository):
    doing = make_task_row(status=TaskStatus.IN_PROGRESS.value)
    make_task_row(status=TaskStatus.TODO.value)

    assert ids(repository, TaskFilter(status=TaskStatus.IN_PROGRESS)) == [doing.pk]


def test_filters_by_assignee(repository):
    alice = make_user()
    mine = make_task_row(assignee=alice)
    make_task_row(assignee=make_user())
    make_task_row(assignee=None)

    assert ids(repository, TaskFilter(assignee_id=alice.pk)) == [mine.pk]


def test_due_after_and_due_before_include_the_boundary_dates(repository):
    on_start = make_task_row(due_date=YESTERDAY)
    on_end = make_task_row(due_date=TOMORROW)
    make_task_row(due_date=YESTERDAY - timedelta(days=1))
    make_task_row(due_date=TOMORROW + timedelta(days=1))
    make_task_row(due_date=None)

    found = ids(repository, TaskFilter(due_after=YESTERDAY, due_before=TOMORROW))

    assert found == [on_start.pk, on_end.pk]


def test_overdue_means_due_before_today_and_not_done(repository):
    overdue = make_task_row(due_date=YESTERDAY, status=TaskStatus.IN_PROGRESS.value)
    make_task_row(due_date=TODAY)
    make_task_row(due_date=YESTERDAY, status=TaskStatus.DONE.value)
    make_task_row(due_date=None)

    assert ids(repository, TaskFilter(overdue=True)) == [overdue.pk]


def test_not_overdue_is_everything_else(repository):
    make_task_row(due_date=YESTERDAY, status=TaskStatus.TODO.value)
    due_today = make_task_row(due_date=TODAY)
    done_late = make_task_row(due_date=YESTERDAY, status=TaskStatus.DONE.value)
    no_date = make_task_row(due_date=None)

    found = ids(repository, TaskFilter(overdue=False))

    assert found == [done_late.pk, due_today.pk, no_date.pk]


def test_filters_combine_with_and(repository):
    alice = make_user()
    match = make_task_row(assignee=alice, status=TaskStatus.TODO.value, due_date=TOMORROW)
    make_task_row(assignee=alice, status=TaskStatus.DONE.value, due_date=TOMORROW)
    make_task_row(assignee=make_user(), status=TaskStatus.TODO.value, due_date=TOMORROW)

    found = ids(
        repository,
        TaskFilter(status=TaskStatus.TODO, assignee_id=alice.pk, due_after=TODAY),
    )

    assert found == [match.pk]


class TestPaging:
    @pytest.fixture
    def fifteen(self) -> list[int]:
        creator = make_user()
        return [
            make_task_row(created_by=creator, due_date=TODAY + timedelta(days=n)).pk
            for n in range(15)
        ]

    def test_returns_the_requested_page_and_the_total(self, repository, fifteen):
        page = repository.find(TaskFilter(), PageRequest(page=2, page_size=10), today=TODAY)

        assert [task.id for task in page.items] == fifteen[10:]
        assert page.total == 15
        assert page.has_next is False

    def test_a_page_past_the_end_is_empty_and_keeps_the_total(self, repository, fifteen):
        page = repository.find(TaskFilter(), PageRequest(page=5, page_size=10), today=TODAY)

        assert page.items == []
        assert page.total == 15

    def test_uses_two_queries_however_many_rows(
        self, repository, fifteen, django_assert_num_queries
    ):
        # One COUNT and one SELECT for the page: no query per task (no N+1).
        with django_assert_num_queries(2):
            page = repository.find(TaskFilter(), PageRequest(page_size=100), today=TODAY)

        assert len(page.items) == 15
