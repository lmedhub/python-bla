"""CeleryNotifier against the real Redis broker of the test settings (database 1)."""

import base64
import json
import logging
import time
from collections.abc import Iterator

import pytest
import redis
from celery import Celery
from django.conf import settings
from django.db import transaction

from apps.tasks.infrastructure.notifications import ASSIGNMENT_JOB, CeleryNotifier
from config.celery import app

# on_commit needs a database transaction, even though nothing is written.
pytestmark = pytest.mark.django_db

# Celery's default queue is a Redis list with this name.
QUEUE = "celery"
# Nothing listens here, so connecting fails at once.
CLOSED_PORT_BROKER = "redis://127.0.0.1:1/0"
# Bounds the "Redis down" case without making the test depend on exact timings.
MAX_SECONDS_WHEN_REDIS_IS_DOWN = 5


@pytest.fixture
def broker() -> Iterator[redis.Redis]:
    client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
    client.delete(QUEUE)
    yield client
    client.delete(QUEUE)
    client.close()


def queued_jobs(broker: redis.Redis) -> list[tuple[str, list[object]]]:
    """(job name, args) of each message waiting in the queue."""
    jobs = []
    for raw in broker.lrange(QUEUE, 0, -1):
        message = json.loads(raw)
        args, _kwargs, _embed = json.loads(base64.b64decode(message["body"]))
        jobs.append((message["headers"]["task"], args))
    return jobs


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


@pytest.fixture
def app_with_redis_down() -> Iterator[Celery]:
    down = Celery("redis-down", set_as_current=False)
    down.config_from_object("django.conf:settings", namespace="CELERY")
    down.conf.broker_url = CLOSED_PORT_BROKER
    yield down
    down.close()


def test_when_redis_is_down_it_logs_and_returns_quickly(
    app_with_redis_down, django_capture_on_commit_callbacks, caplog
):
    started = time.monotonic()
    with caplog.at_level(logging.ERROR), django_capture_on_commit_callbacks(execute=True):
        CeleryNotifier(app_with_redis_down).task_assigned(task_id=7, assignee_id=3)
    elapsed = time.monotonic() - started

    assert "on_commit" in caplog.text
    assert elapsed < MAX_SECONDS_WHEN_REDIS_IS_DOWN
