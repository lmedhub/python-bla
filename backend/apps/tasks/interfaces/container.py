"""Composition root for tasks: the only interfaces module allowed to import infrastructure."""

from datetime import date, tzinfo

from apps.core.infrastructure.clock import SystemClock
from apps.tasks.application.ports import Clock, Notifier
from apps.tasks.application.use_cases import CreateTask, DeleteTask, GetTask, ListTasks, UpdateTask
from apps.tasks.infrastructure.clock import ZonedClock
from apps.tasks.infrastructure.notifications import LoggingNotifier
from apps.tasks.infrastructure.repositories import DjangoTaskRepository
from apps.tasks.infrastructure.user_directory import DjangoUserDirectory

# Module attributes, read on every call, so tests can swap in a fixed clock.
clock: Clock = SystemClock()
# Logs only for now; Phase 4 replaces it with a Celery notifier.
notifier: Notifier = LoggingNotifier()


def today(zone: tzinfo) -> date:
    return _clock_for(zone).today()


def create_task(zone: tzinfo) -> CreateTask:
    return CreateTask(
        tasks=_repository(), users=DjangoUserDirectory(), notifier=notifier, clock=_clock_for(zone)
    )


def get_task() -> GetTask:
    return GetTask(tasks=_repository())


def list_tasks(zone: tzinfo) -> ListTasks:
    return ListTasks(tasks=_repository(), clock=_clock_for(zone))


def update_task() -> UpdateTask:
    return UpdateTask(
        tasks=_repository(), users=DjangoUserDirectory(), notifier=notifier, clock=clock
    )


def delete_task() -> DeleteTask:
    return DeleteTask(tasks=_repository())


def _repository() -> DjangoTaskRepository:
    # Timestamps are instants, so the repository uses the plain clock.
    return DjangoTaskRepository(clock=clock)


def _clock_for(zone: tzinfo) -> Clock:
    # "Today" is the caller's date; the use cases do not know or care where that came from.
    return ZonedClock(clock, zone)
