import pytest

from apps.tasks.tests.fakes import (
    FakeUserDirectory,
    FixedClock,
    InMemoryTaskRepository,
    RecordingNotifier,
)

from .constants import ASSIGNEE, CREATOR, NOW, STRANGER


@pytest.fixture
def tasks() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


@pytest.fixture
def users() -> FakeUserDirectory:
    return FakeUserDirectory(active_user_ids={CREATOR, ASSIGNEE, STRANGER})


@pytest.fixture
def notifier() -> RecordingNotifier:
    return RecordingNotifier()


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)
