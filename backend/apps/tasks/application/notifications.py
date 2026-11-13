"""Use cases run by background jobs: they send email, so they never run inside a request.

Both follow "check, send, record" with a key per email (ADR 0012). A retry or a duplicate
delivery finds the key and sends nothing. A crash between send and record can send one
email twice, but never loses one.
"""

from collections import defaultdict
from datetime import date
from enum import StrEnum

from apps.tasks.application.ports import Clock, Mailer, SentLog, TaskRepository, UserDirectory
from apps.tasks.domain.task import Task


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
        # The message id stays the same across retries, and differs for each assignment.
        key = f"assignment:{message_id}"
        if self._sent_log.was_sent(key):
            return Delivery.ALREADY_SENT

        # The job runs after the request: re-read what is true now, not what was enqueued.
        task = self._tasks.get(task_id)
        if task is None:
            return Delivery.TASK_DELETED
        if task.assignee_id != assignee_id:
            return Delivery.REASSIGNED
        recipient = self._users.active_recipients([assignee_id]).get(assignee_id)
        if recipient is None:
            return Delivery.ASSIGNEE_INACTIVE

        self._mailer.send(
            to=recipient.email,
            subject=f'You were assigned "{task.title}"',
            body=(
                f"Hi {recipient.name},\n\n"
                f'You were assigned the task "{task.title}".\n'
                f"Due: {_format_date(task.due_date)}\n"
            ),
        )
        self._sent_log.record(key)
        return Delivery.SENT


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
        today = self._clock.today()
        overdue_by_assignee: dict[int, list[Task]] = defaultdict(list)
        for task in self._tasks.list_overdue(today):
            if task.assignee_id is not None:
                overdue_by_assignee[task.assignee_id].append(task)
        # One lookup for everyone, not one per assignee.
        recipients = self._users.active_recipients(overdue_by_assignee.keys())

        sent = 0
        for assignee_id, overdue in overdue_by_assignee.items():
            recipient = recipients.get(assignee_id)
            # One digest per person per day, however often the job runs.
            key = f"digest:{assignee_id}:{today.isoformat()}"
            if recipient is None or self._sent_log.was_sent(key):
                continue
            self._mailer.send(
                to=recipient.email,
                subject=f"You have {_count(len(overdue), 'overdue task')}",
                body=(
                    f"Hi {recipient.name},\n\n"
                    "These tasks are past their due date:\n\n"
                    + "".join(_digest_line(task) for task in overdue)
                ),
            )
            self._sent_log.record(key)
            sent += 1
        return sent


def _digest_line(task: Task) -> str:
    return f"- {task.title} (due {_format_date(task.due_date)})\n"


def _format_date(value: date | None) -> str:
    # ISO dates: unambiguous for every reader, whatever their locale.
    return value.isoformat() if value else "no due date"


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"
