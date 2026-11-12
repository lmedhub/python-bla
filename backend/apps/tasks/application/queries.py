from dataclasses import dataclass
from datetime import date

from apps.core.domain.errors import InvalidInputError
from apps.tasks.domain.task import TaskStatus

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class TaskFilter:
    """Every field is optional; None means "do not filter on this"."""

    status: TaskStatus | None = None
    due_after: date | None = None
    due_before: date | None = None
    assignee_id: int | None = None
    overdue: bool | None = None


@dataclass(frozen=True)
class PageRequest:
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        errors: dict[str, list[str]] = {}
        if self.page < 1:
            errors["page"] = ["Must be 1 or more."]
        if not 1 <= self.page_size <= MAX_PAGE_SIZE:
            errors["page_size"] = [f"Must be between 1 and {MAX_PAGE_SIZE}."]
        if errors:
            raise InvalidInputError(errors)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    total: int
    request: PageRequest

    @property
    def has_next(self) -> bool:
        return self.request.offset + len(self.items) < self.total

    @property
    def has_previous(self) -> bool:
        return self.request.page > 1
