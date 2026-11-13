"""Use cases run by background jobs: they send email, so they never run inside a request."""

from enum import StrEnum

from apps.tasks.application.ports import Clock, Mailer, SentLog, TaskRepository, UserDirectory


class Delivery(StrEnum):
    SENT = "sent"
    ALREADY_SENT = "already_sent"
    TASK_DELETED = "task_deleted"
    REASSIGNED = "reassigned"
    ASSIGNEE_INACTIVE = "assignee_inactive"


class NotifyAssignment:
    def __init__(
        self, tasks: TaskRepository, users: UserDirectory, mailer: Mailer, sent_log: SentLog
    ) -> None:
        self._tasks = tasks
        self._users = users
        self._mailer = mailer
        self._sent_log = sent_log

    def execute(self, task_id: int, assignee_id: int, message_id: str) -> Delivery:
        raise NotImplementedError


class SendOverdueDigests:
    def __init__(
        self,
        tasks: TaskRepository,
        users: UserDirectory,
        mailer: Mailer,
        sent_log: SentLog,
        clock: Clock,
    ) -> None:
        self._tasks = tasks
        self._users = users
        self._mailer = mailer
        self._sent_log = sent_log
        self._clock = clock

    def execute(self) -> int:
        """Sends one email per assignee with overdue tasks. Returns how many were sent."""
        raise NotImplementedError
