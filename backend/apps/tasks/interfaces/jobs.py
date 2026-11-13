"""Celery jobs: the worker's entry points, like views are the API's. They only call use cases."""

import logging

from celery import Task
from config.celery import app

from apps.tasks.interfaces import container

logger = logging.getLogger(__name__)

# smtplib errors and refused connections are all OSErrors: retry those, waiting longer each
# time (about 1 s, 2 s, 4 s, ... up to 10 min, with jitter so retries do not bunch up).
RETRY_POLICY = {
    "autoretry_for": (OSError,),
    "retry_backoff": True,
    "retry_backoff_max": 600,
    "retry_jitter": True,
    "max_retries": 5,
}


@app.task(bind=True, name=container.ASSIGNMENT_JOB, **RETRY_POLICY)
def notify_assignment(self: Task, task_id: int, assignee_id: int) -> str:
    # The message id is the same on every retry of this job, so it is the idempotency key.
    delivery = container.notify_assignment().execute(task_id, assignee_id, self.request.id)
    logger.info("Assignment email for task %s to user %s: %s.", task_id, assignee_id, delivery)
    return delivery.value


@app.task(name=container.DIGEST_JOB, **RETRY_POLICY)
def send_overdue_digests() -> int:
    sent = container.send_overdue_digests().execute()
    logger.info("Overdue digest: %s email(s) sent.", sent)
    return sent
