"""The API queues the assignment email through the real CeleryNotifier."""

import logging
import time

import pytest

from apps.tasks.infrastructure.models import Task
from apps.tasks.infrastructure.notifications import ASSIGNMENT_JOB, CeleryNotifier
from apps.tasks.interfaces import container
from apps.tasks.tests.broker import MAX_SECONDS_WHEN_REDIS_IS_DOWN, queued_jobs
from apps.users.tests.factories import make_user

TASKS_URL = "/api/v1/tasks"


@pytest.mark.django_db
def test_assigning_a_task_queues_the_email_once_the_request_commits(
    login_as, alice, bob, broker, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = login_as(alice).post(
            TASKS_URL, {"title": "Pay invoices", "assignee": bob.pk}, format="json"
        )

    assert response.status_code == 201
    assert queued_jobs(broker) == [(ASSIGNMENT_JOB, [response.data["id"], bob.pk])]


# transaction=True: the request really commits, so on_commit runs inside the request,
# exactly as in production. A test transaction would defer it until after the response.
@pytest.mark.django_db(transaction=True)
def test_when_redis_is_down_assigning_still_succeeds_quickly(
    login_as, monkeypatch, app_with_redis_down, caplog
):
    alice = make_user(email="alice@example.com")
    bob = make_user(email="bob@example.com")
    monkeypatch.setattr(container, "notifier", CeleryNotifier(app_with_redis_down))

    started = time.monotonic()
    with caplog.at_level(logging.ERROR):
        response = login_as(alice).post(
            TASKS_URL, {"title": "Pay invoices", "assignee": bob.pk}, format="json"
        )
    elapsed = time.monotonic() - started

    assert response.status_code == 201
    assert Task.objects.filter(pk=response.data["id"], assignee_id=bob.pk).exists()
    assert "on_commit" in caplog.text
    assert elapsed < MAX_SECONDS_WHEN_REDIS_IS_DOWN
