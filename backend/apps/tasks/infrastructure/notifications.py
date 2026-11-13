import logging

from celery import Celery

logger = logging.getLogger(__name__)


class LoggingNotifier:
    """Writes the assignment to the log. Phase 4 adds the e-mail through Celery."""

    def task_assigned(self, task_id: int, assignee_id: int) -> None:
        logger.info("Task %s was assigned to user %s.", task_id, assignee_id)


# Job names are the contract between the sender (here) and the worker (interfaces/jobs.py).
ASSIGNMENT_JOB = "tasks.notify_assignment"
DIGEST_JOB = "tasks.send_overdue_digests"


class CeleryNotifier:
    def __init__(self, app: Celery) -> None:
        self._app = app

    def task_assigned(self, task_id: int, assignee_id: int) -> None:
        raise NotImplementedError
