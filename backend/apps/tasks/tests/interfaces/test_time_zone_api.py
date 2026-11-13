"""Seen in the manual run: 21:21 in Sao Paulo is already 00:21 the next day in UTC.

"Today" must be the caller's date, sent as an IANA zone name in X-Timezone.
"""

from datetime import UTC, date, datetime

import pytest

from apps.tasks.tests.factories import make_task_row

pytestmark = pytest.mark.django_db

TASKS = "/api/v1/tasks"
LATE_EVENING_IN_BRAZIL = datetime(2026, 11, 13, 0, 21, tzinfo=UTC)
LOCAL_TODAY = date(2026, 11, 12)
BRAZIL = {"HTTP_X_TIMEZONE": "America/Sao_Paulo"}


@pytest.fixture(autouse=True)
def evening_in_brazil(clock):
    clock.current = LATE_EVENING_IN_BRAZIL


def test_a_task_due_today_in_the_callers_zone_can_be_created(login_as, alice):
    response = login_as(alice).post(
        TASKS, {"title": "Tonight", "due_date": str(LOCAL_TODAY)}, format="json", **BRAZIL
    )

    assert response.status_code == 201
    assert response.json()["is_overdue"] is False


def test_without_the_header_utc_decides_and_the_same_date_is_in_the_past(login_as, alice):
    response = login_as(alice).post(
        TASKS, {"title": "Tonight", "due_date": str(LOCAL_TODAY)}, format="json"
    )

    assert response.status_code == 400
    assert list(response.json()["fields"]) == ["due_date"]


def test_a_task_due_today_is_not_overdue_for_the_caller(login_as, alice):
    task = make_task_row(created_by=alice, due_date=LOCAL_TODAY)
    client = login_as(alice)

    assert client.get(f"{TASKS}/{task.pk}", **BRAZIL).json()["is_overdue"] is False
    assert client.get(f"{TASKS}/{task.pk}").json()["is_overdue"] is True


def test_the_overdue_filter_uses_the_callers_date(login_as, alice):
    make_task_row(created_by=alice, due_date=LOCAL_TODAY)
    client = login_as(alice)

    assert client.get(TASKS, {"overdue": "true"}, **BRAZIL).json()["count"] == 0
    assert client.get(TASKS, {"overdue": "true"}).json()["count"] == 1


def test_an_unknown_zone_is_a_400_on_the_header(login_as, alice):
    response = login_as(alice).get(TASKS, HTTP_X_TIMEZONE="Mars/Olympus_Mons")

    assert response.status_code == 400
    assert list(response.json()["fields"]) == ["X-Timezone"]
