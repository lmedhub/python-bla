from dataclasses import dataclass
from datetime import date

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
        raise NotImplementedError

    @property
    def offset(self) -> int:
        raise NotImplementedError


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    total: int
    request: PageRequest

    @property
    def has_next(self) -> bool:
        raise NotImplementedError

    @property
    def has_previous(self) -> bool:
        raise NotImplementedError
