"""Create, read, update and delete over HTTP. Alice creates, Bob is assigned, Carol is neither."""

import logging
from datetime import timedelta

import pytest

from apps.tasks.tests.application.constants import NOW
from apps.tasks.tests.factories import make_task_row
from apps.users.tests.factories import make_user

pytestmark = pytest.mark.django_db

TASKS = "/api/v1/tasks"
TODAY = NOW.date()
FIELDS = {
    "id",
    "title",
    "description",
    "status",
    "due_date",
    "created_by",
    "assignee",
    "completed_at",
    "created_at",
    "updated_at",
    "version",
    "is_overdue",
}


def item(task_id: int) -> str:
    return f"{TASKS}/{task_id}"


@pytest.fixture
def task(alice, bob):
    """Alice's task, assigned to Bob."""
    return make_task_row(created_by=alice, assignee=bob)


class TestCreate:
    def test_creates_a_todo_task_owned_by_the_caller(self, login_as, alice):
        response = login_as(alice).post(
            TASKS,
            {"title": "  Write tests ", "description": "All of them", "due_date": str(TODAY)},
            format="json",
        )

        assert response.status_code == 201
        body = response.json()
        assert set(body) == FIELDS
        assert body["title"] == "Write tests"
        assert body["status"] == "todo"
        assert body["created_by"] == alice.pk
        assert body["assignee"] is None
        assert body["version"] == 1
        assert body["is_overdue"] is False
        assert body["created_at"] == "2026-11-12T09:30:00Z"

    def test_assigning_on_create_logs_a_notification(self, login_as, alice, bob, caplog):
        with caplog.at_level(logging.INFO):
            response = login_as(alice).post(
                TASKS, {"title": "Review", "assignee": bob.pk}, format="json"
            )

        assert response.status_code == 201
        assert response.json()["assignee"] == bob.pk
        assert f"assigned to user {bob.pk}" in caplog.text

    @pytest.mark.parametrize("title", ["", "   ", "x" * 201])
    def test_rejects_blank_whitespace_or_too_long_titles(self, login_as, alice, title):
        response = login_as(alice).post(TASKS, {"title": title}, format="json")

        assert response.status_code == 400
        assert response.json()["code"] == "invalid_input"
        assert list(response.json()["fields"]) == ["title"]

    def test_requires_a_title(self, login_as, alice):
        response = login_as(alice).post(TASKS, {}, format="json")

        assert response.status_code == 400
        assert list(response.json()["fields"]) == ["title"]

    def test_rejects_a_due_date_in_the_past(self, login_as, alice):
        yesterday = str(TODAY - timedelta(days=1))

        response = login_as(alice).post(
            TASKS, {"title": "Late", "due_date": yesterday}, format="json"
        )

        assert response.status_code == 400
        assert list(response.json()["fields"]) == ["due_date"]

    def test_rejects_an_unknown_assignee_as_a_field_error(self, login_as, alice):
        response = login_as(alice).post(TASKS, {"title": "X", "assignee": 999_999}, format="json")

        assert response.status_code == 400
        assert list(response.json()["fields"]) == ["assignee"]

    def test_rejects_an_inactive_assignee(self, login_as, alice):
        gone = make_user(is_active=False)

        response = login_as(alice).post(TASKS, {"title": "X", "assignee": gone.pk}, format="json")

        assert response.status_code == 400
        assert list(response.json()["fields"]) == ["assignee"]

    def test_requires_authentication(self, api_client):
        assert api_client.post(TASKS, {"title": "X"}, format="json").status_code == 401


class TestRead:
    def test_any_signed_in_user_can_read_a_task(self, login_as, carol, task):
        response = login_as(carol).get(item(task.pk))

        assert response.status_code == 200
        assert response.json()["id"] == task.pk

    def test_a_past_due_open_task_is_overdue(self, login_as, alice):
        late = make_task_row(created_by=alice, due_date=TODAY - timedelta(days=1))

        assert login_as(alice).get(item(late.pk)).json()["is_overdue"] is True

    def test_unknown_task_is_404(self, login_as, alice):
        response = login_as(alice).get(item(999_999))

        assert response.status_code == 404
        assert response.json()["code"] == "not_found"


class TestUpdate:
    def test_creator_can_edit_any_field_and_the_version_goes_up(self, login_as, alice, task):
        response = login_as(alice).patch(
            item(task.pk), {"title": "Renamed", "assignee": None}, format="json"
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Renamed"
        assert response.json()["assignee"] is None
        assert response.json()["version"] == 2

    def test_assignee_can_complete_the_task(self, login_as, bob, task):
        response = login_as(bob).patch(item(task.pk), {"status": "done"}, format="json")

        assert response.status_code == 200
        assert response.json()["status"] == "done"
        assert response.json()["completed_at"] == "2026-11-12T09:30:00Z"

    def test_completing_twice_keeps_the_first_completion_time(self, login_as, bob, task, clock):
        client = login_as(bob)
        client.patch(item(task.pk), {"status": "done"}, format="json")
        clock.advance(timedelta(hours=3))

        response = client.patch(item(task.pk), {"status": "done"}, format="json")

        assert response.json()["completed_at"] == "2026-11-12T09:30:00Z"

    def test_assignee_cannot_rename_the_task(self, login_as, bob, task):
        response = login_as(bob).patch(item(task.pk), {"title": "Mine"}, format="json")

        assert response.status_code == 403
        assert response.json()["code"] == "permission_denied"

    def test_others_cannot_change_the_status(self, login_as, carol, task):
        response = login_as(carol).patch(item(task.pk), {"status": "done"}, format="json")

        assert response.status_code == 403

    def test_others_get_403_not_a_validation_error(self, login_as, carol, task):
        response = login_as(carol).patch(item(task.pk), {"title": "   "}, format="json")

        assert response.status_code == 403

    def test_a_stale_version_is_409_and_nothing_changes(self, login_as, alice, task):
        client = login_as(alice)
        client.patch(item(task.pk), {"title": "First", "version": 1}, format="json")

        response = client.patch(item(task.pk), {"title": "Second", "version": 1}, format="json")

        assert response.status_code == 409
        assert response.json()["code"] == "conflict"
        assert client.get(item(task.pk)).json()["title"] == "First"

    def test_the_current_version_is_accepted(self, login_as, alice, task):
        response = login_as(alice).patch(
            item(task.pk), {"title": "Fresh", "version": 1}, format="json"
        )

        assert response.status_code == 200

    def test_rejects_an_unknown_status(self, login_as, alice, task):
        response = login_as(alice).patch(item(task.pk), {"status": "archived"}, format="json")

        assert response.status_code == 400
        assert list(response.json()["fields"]) == ["status"]

    def test_rejects_an_unknown_assignee(self, login_as, alice, task):
        response = login_as(alice).patch(item(task.pk), {"assignee": 999_999}, format="json")

        assert response.status_code == 400
        assert list(response.json()["fields"]) == ["assignee"]

    def test_unknown_task_is_404(self, login_as, alice):
        assert login_as(alice).patch(item(999_999), {}, format="json").status_code == 404

    def test_requires_authentication(self, api_client, task):
        assert api_client.patch(item(task.pk), {}, format="json").status_code == 401


class TestDelete:
    def test_creator_deletes_the_task(self, login_as, alice, task):
        client = login_as(alice)

        assert client.delete(item(task.pk)).status_code == 204
        assert client.get(item(task.pk)).status_code == 404

    @pytest.mark.parametrize("who", ["bob", "carol"])
    def test_nobody_else_may_delete(self, login_as, task, who, request):
        response = login_as(request.getfixturevalue(who)).delete(item(task.pk))

        assert response.status_code == 403

    def test_unknown_task_is_404(self, login_as, alice):
        assert login_as(alice).delete(item(999_999)).status_code == 404
