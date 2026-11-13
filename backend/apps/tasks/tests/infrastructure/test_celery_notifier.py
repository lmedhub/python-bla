import logging
import time

import pytest
from django.db import transaction

from apps.tasks.infrastructure.notifications import ASSIGNMENT_JOB, CeleryNotifier
from apps.tasks.tests.broker import MAX_SECONDS_WHEN_REDIS_IS_DOWN, queued_jobs
from config.celery import app

# on_commit needs a database transaction, even though nothing is written.
pytestmark = pytest.mark.django_db


def test_publishes_ids_only_after_the_transaction_commits(
    broker, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        CeleryNotifier(app).task_assigned(task_id=7, assignee_id=3)
        # Still inside the transaction: nothing may be sent yet.
        assert queued_jobs(broker) == []

    assert queued_jobs(broker) == [(ASSIGNMENT_JOB, [7, 3])]


class RollbackError(Exception):
    pass


def assign_then_fail() -> None:
    with transaction.atomic():
        CeleryNotifier(app).task_assigned(task_id=7, assignee_id=3)
        raise RollbackError


def test_publishes_nothing_when_the_transaction_rolls_back(
    broker, django_capture_on_commit_callbacks
):
    with (
        django_capture_on_commit_callbacks(execute=True) as callbacks,
        pytest.raises(RollbackError),
    ):
        assign_then_fail()

    assert callbacks == []
    assert queued_jobs(broker) == []


def test_when_redis_is_down_it_logs_and_returns_quickly(
    app_with_redis_down, django_capture_on_commit_callbacks, caplog
):
    started = time.monotonic()
    with caplog.at_level(logging.ERROR), django_capture_on_commit_callbacks(execute=True):
        CeleryNotifier(app_with_redis_down).task_assigned(task_id=7, assignee_id=3)
    elapsed = time.monotonic() - started

    assert "on_commit" in caplog.text
    assert elapsed < MAX_SECONDS_WHEN_REDIS_IS_DOWN
