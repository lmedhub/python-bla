"""Reads what CeleryNotifier put on the real Redis broker of the test settings (database 1)."""

import base64
import json

import redis

# Celery's default queue is a Redis list with this name.
QUEUE = "celery"
# Nothing listens here, so connecting fails at once.
CLOSED_PORT_BROKER = "redis://127.0.0.1:1/0"
# Bounds the "Redis down" cases without making tests depend on exact timings.
MAX_SECONDS_WHEN_REDIS_IS_DOWN = 5


def queued_jobs(broker: redis.Redis) -> list[tuple[str, list[object]]]:
    """(job name, args) of each message waiting in the queue."""
    jobs = []
    for raw in broker.lrange(QUEUE, 0, -1):
        message = json.loads(raw)
        args, _kwargs, _embed = json.loads(base64.b64decode(message["body"]))
        jobs.append((message["headers"]["task"], args))
    return jobs
