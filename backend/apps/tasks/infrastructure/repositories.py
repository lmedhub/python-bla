from datetime import date

from apps.tasks.application.ports import Clock
from apps.tasks.application.queries import Page, PageRequest, TaskFilter
from apps.tasks.domain.task import Task


class DjangoTaskRepository:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def get(self, task_id: int) -> Task | None:
        raise NotImplementedError

    def add(self, task: Task) -> Task:
        raise NotImplementedError

    def update(self, task: Task) -> Task:
        raise NotImplementedError

    def delete(self, task_id: int) -> None:
        raise NotImplementedError

    def find(self, task_filter: TaskFilter, page: PageRequest, today: date) -> Page[Task]:
        raise NotImplementedError
