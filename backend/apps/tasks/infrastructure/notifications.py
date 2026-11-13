import logging

logger = logging.getLogger(__name__)


class LoggingNotifier:
    """Writes the assignment to the log. Phase 4 adds the e-mail through Celery."""

    def task_assigned(self, task_id: int, assignee_id: int) -> None:
        logger.info("Task %s was assigned to user %s.", task_id, assignee_id)
