"""In-memory fakes of the tasks ports. Typed, so mypy checks they match the Protocols."""

from collections.abc import Collection
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta

from apps.core.domain.errors import ConflictError
from apps.tasks.application.ports import Recipient
from apps.tasks.application.queries import Page, PageRequest, TaskFilter
from apps.tasks.domain.task import Task


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current

    def today(self) -> date:
        return self.current.date()

    def advance(self, delta: timedelta) -> None:
        self.current += delta


class InMemoryTaskRepository:
    """Stores copies, like a database would, so unsaved changes never leak into storage."""

    def __init__(self) -> None:
        self.rows: dict[int, Task] = {}
        self.find_calls: list[tuple[TaskFilter, PageRequest, date]] = []
        self._next_id = 1

    def get(self, task_id: int) -> Task | None:
        row = self.rows.get(task_id)
        return replace(row) if row else None

    def add(self, task: Task) -> Task:
        saved = replace(task, id=self._next_id)
        self._next_id += 1
        self.rows[saved.require_id()] = saved
        return replace(saved)

    def update(self, task: Task) -> Task:
        if self.rows[task.require_id()].version != task.version:
            raise ConflictError("Task was changed by someone else.")
        saved = replace(task, version=task.version + 1)
        self.rows[task.require_id()] = saved
        return replace(saved)

    def delete(self, task_id: int) -> None:
        del self.rows[task_id]

    def find(self, task_filter: TaskFilter, page: PageRequest, today: date) -> Page[Task]:
        # Filtering is tested against Postgres in the repository tests. Copying it here
        # would only test the copy, so the fake just records what the use case asked for.
        self.find_calls.append((task_filter, page, today))
        return Page(items=[], total=0, request=page)

    def list_overdue(self, today: date) -> list[Task]:
        # The overdue rule itself is the domain's; the SQL version is tested against Postgres.
        overdue = [replace(task) for task in self.rows.values() if task.is_overdue(today)]
        return sorted(overdue, key=lambda task: (task.due_date, task.id))


class FakeUserDirectory:
    def __init__(self, active_user_ids: set[int]) -> None:
        self.active_user_ids = active_user_ids

    def is_active_user(self, user_id: int) -> bool:
        return user_id in self.active_user_ids

    def active_recipients(self, user_ids: Collection[int]) -> dict[int, Recipient]:
        return {
            user_id: recipient_for(user_id)
            for user_id in user_ids
            if user_id in self.active_user_ids
        }


def recipient_for(user_id: int) -> Recipient:
    return Recipient(email=f"user{user_id}@example.com", name=f"User {user_id}")


class RecordingNotifier:
    def __init__(self) -> None:
        self.assignments: list[tuple[int, int]] = []

    def task_assigned(self, task_id: int, assignee_id: int) -> None:
        self.assignments.append((task_id, assignee_id))


@dataclass(frozen=True)
class SentEmail:
    to: str
    subject: str
    body: str


class OutboxMailer:
    def __init__(self) -> None:
        self.outbox: list[SentEmail] = []

    def send(self, *, to: str, subject: str, body: str) -> None:
        self.outbox.append(SentEmail(to=to, subject=subject, body=body))


class BrokenMailer:
    """Fails like an unreachable SMTP server does (smtplib errors are OSErrors)."""

    def send(self, *, to: str, subject: str, body: str) -> None:
        raise ConnectionRefusedError("SMTP server is down")


class InMemorySentLog:
    def __init__(self) -> None:
        self.keys: set[str] = set()

    def was_sent(self, key: str) -> bool:
        return key in self.keys

    def record(self, key: str) -> None:
        self.keys.add(key)
