from collections.abc import Set
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


# The assignee may move the task along, but only the creator may change what the task is.
ASSIGNEE_EDITABLE_FIELDS = frozenset({"status"})


@dataclass
class Task:
    title: str
    created_by_id: int
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    due_date: date | None = None
    assignee_id: int | None = None
    completed_at: datetime | None = None
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def change_status(self, new_status: TaskStatus, now: datetime) -> None:
        if new_status is not TaskStatus.DONE:
            self.completed_at = None
        elif self.status is not TaskStatus.DONE:
            # Only the first completion counts: repeating "done" must not move the timestamp.
            self.completed_at = now
        self.status = new_status

    def is_overdue(self, today: date) -> bool:
        return (
            self.due_date is not None
            and self.due_date < today
            and self.status is not TaskStatus.DONE
        )

    def can_be_updated_by(self, actor_id: int, changed_fields: Set[str]) -> bool:
        if actor_id == self.created_by_id:
            return True
        if actor_id == self.assignee_id:
            return changed_fields <= ASSIGNEE_EDITABLE_FIELDS
        return False

    def can_be_deleted_by(self, actor_id: int) -> bool:
        return actor_id == self.created_by_id

    def require_id(self) -> int:
        if self.id is None:
            raise RuntimeError("Task has not been saved yet.")
        return self.id
