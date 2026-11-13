from functools import partial

from celery import Celery
from django.db import transaction

# Job names are the contract between the sender (here) and the worker (interfaces/jobs.py).
ASSIGNMENT_JOB = "tasks.notify_assignment"
DIGEST_JOB = "tasks.send_overdue_digests"


class CeleryNotifier:
    """Queues the assignment email for the worker. Never fails or blocks the request.

    on_commit: a rolled-back request sends nothing, and the worker always finds the saved
    task. robust=True: if Redis is down, Django logs the error and the request still
    succeeds (ADR 0005). The notification is then lost; the log line says so.
    """

    def __init__(self, app: Celery) -> None:
        self._app = app

    def task_assigned(self, task_id: int, assignee_id: int) -> None:
        transaction.on_commit(partial(self._publish, task_id, assignee_id), robust=True)

    def _publish(self, task_id: int, assignee_id: int) -> None:
        # By name, so this module does not import the job (interfaces imports infrastructure,
        # never the reverse). IDs only: the worker re-reads the current state.
        self._app.send_task(ASSIGNMENT_JOB, args=[task_id, assignee_id])
