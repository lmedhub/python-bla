from collections.abc import Set
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


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
        raise NotImplementedError

    def is_overdue(self, today: date) -> bool:
        raise NotImplementedError

    def can_be_updated_by(self, actor_id: int, changed_fields: Set[str]) -> bool:
        raise NotImplementedError

    def can_be_deleted_by(self, actor_id: int) -> bool:
        raise NotImplementedError

    def require_id(self) -> int:
        raise NotImplementedError
