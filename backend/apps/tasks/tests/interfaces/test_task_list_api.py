from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.tasks.domain.task import TaskStatus
from apps.tasks.tests.application.constants import NOW
from apps.tasks.tests.factories import make_task_row

pytestmark = pytest.mark.django_db

TASKS = "/api/v1/tasks"
TODAY = NOW.date()


def ids(response) -> list[int]:
    return [task["id"] for task in response.json()["results"]]


class TestPagination:
    @pytest.fixture
    def twelve(self, alice) -> list[int]:
        return [
            make_task_row(created_by=alice, due_date=TODAY + timedelta(days=n)).pk
            for n in range(12)
        ]

    def test_first_page_has_ten_results_and_a_next_link(self, login_as, alice, twelve):
        response = login_as(alice).get(TASKS)

        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"count", "next", "previous", "results"}
        assert body["count"] == 12
        assert ids(response) == twelve[:10]
        assert body["next"] == "/api/v1/tasks?page=2"
        assert body["previous"] is None

    def test_links_keep_the_filters(self, login_as, alice, twelve):
        body = login_as(alice).get(TASKS, {"status": "todo", "page_size": 5}).json()

        assert body["next"] == "/api/v1/tasks?status=todo&page_size=5&page=2"

    def test_last_page(self, login_as, alice, twelve):
        body = login_as(alice).get(TASKS, {"page": 2}).json()

        assert [task["id"] for task in body["results"]] == twelve[10:]
        assert body["next"] is None
        assert body["previous"] == "/api/v1/tasks?page=1"

    def test_a_page_past_the_end_is_empty_not_404(self, login_as, alice, twelve):
        response = login_as(alice).get(TASKS, {"page": 9})

        assert response.status_code == 200
        assert response.json()["results"] == []
        assert response.json()["count"] == 12

    @pytest.mark.parametrize(
        ("params", "field"),
        [({"page_size": 0}, "page_size"), ({"page_size": 101}, "page_size"), ({"page": 0}, "page")],
    )
    def test_out_of_range_paging_is_400(self, login_as, alice, params, field):
        response = login_as(alice).get(TASKS, params)

        assert response.status_code == 400
        assert list(response.json()["fields"]) == [field]

    def test_no_tasks_is_an_empty_page(self, login_as, alice):
        body = login_as(alice).get(TASKS).json()

        assert body == {"count": 0, "next": None, "previous": None, "results": []}


class TestFilters:
    def test_by_status(self, login_as, alice):
        doing = make_task_row(created_by=alice, status=TaskStatus.IN_PROGRESS.value)
        make_task_row(created_by=alice)

        assert ids(login_as(alice).get(TASKS, {"status": "in_progress"})) == [doing.pk]

    def test_by_due_date_range_inclusive(self, login_as, alice):
        start = make_task_row(created_by=alice, due_date=TODAY)
        end = make_task_row(created_by=alice, due_date=TODAY + timedelta(days=2))
        make_task_row(created_by=alice, due_date=TODAY + timedelta(days=3))

        response = login_as(alice).get(
            TASKS, {"due_after": str(TODAY), "due_before": str(TODAY + timedelta(days=2))}
        )

        assert ids(response) == [start.pk, end.pk]

    def test_by_assignee_id(self, login_as, alice, bob):
        bobs = make_task_row(created_by=alice, assignee=bob)
        make_task_row(created_by=alice, assignee=alice)

        assert ids(login_as(alice).get(TASKS, {"assignee": bob.pk})) == [bobs.pk]

    def test_assignee_me_means_the_caller(self, login_as, alice, bob):
        mine = make_task_row(created_by=alice, assignee=bob)
        make_task_row(created_by=bob, assignee=alice)

        assert ids(login_as(bob).get(TASKS, {"assignee": "me"})) == [mine.pk]

    def test_overdue(self, login_as, alice):
        late = make_task_row(created_by=alice, due_date=TODAY - timedelta(days=1))
        make_task_row(created_by=alice, due_date=TODAY)

        assert ids(login_as(alice).get(TASKS, {"overdue": "true"})) == [late.pk]

    def test_leaving_out_overdue_does_not_filter(self, login_as, alice):
        # DRF treats a missing boolean query parameter as False unless told otherwise.
        late = make_task_row(created_by=alice, due_date=TODAY - timedelta(days=1))
        on_time = make_task_row(created_by=alice, due_date=TODAY)

        assert ids(login_as(alice).get(TASKS)) == [late.pk, on_time.pk]

    @pytest.mark.parametrize(
        ("params", "field"),
        [
            ({"status": "archived"}, "status"),
            ({"due_after": "not-a-date"}, "due_after"),
            ({"assignee": "someone"}, "assignee"),
            ({"assignee": "0"}, "assignee"),
            ({"overdue": "maybe"}, "overdue"),
        ],
    )
    def test_bad_filter_values_are_400(self, login_as, alice, params, field):
        response = login_as(alice).get(TASKS, params)

        assert response.status_code == 400
        assert list(response.json()["fields"]) == [field]


def test_the_list_runs_the_same_queries_for_3_or_15_tasks(login_as, alice):
    client = login_as(alice)

    def count_queries() -> int:
        with CaptureQueriesContext(connection) as queries:
            assert client.get(TASKS, {"page_size": 100}).status_code == 200
        return len(queries)

    for _ in range(3):
        make_task_row(created_by=alice)
    with_three = count_queries()
    for _ in range(12):
        make_task_row(created_by=alice)

    assert count_queries() == with_three


def test_requires_authentication(api_client):
    assert api_client.get(TASKS).status_code == 401
