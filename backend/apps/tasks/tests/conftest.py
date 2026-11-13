from collections.abc import Iterator

import pytest
import redis
from celery import Celery
from django.conf import settings

from apps.tasks.tests.broker import CLOSED_PORT_BROKER, QUEUE


@pytest.fixture
def broker() -> Iterator[redis.Redis]:
    client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
    client.delete(QUEUE)
    yield client
    client.delete(QUEUE)
    client.close()


@pytest.fixture
def app_with_redis_down() -> Iterator[Celery]:
    """The real Celery settings, but a broker that cannot be reached."""
    down = Celery("redis-down", set_as_current=False)
    down.config_from_object("django.conf:settings", namespace="CELERY")
    down.conf.broker_url = CLOSED_PORT_BROKER
    yield down
    down.close()
