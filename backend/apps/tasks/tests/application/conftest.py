import pytest

from apps.tasks.tests.fakes import (
    FakeUserDirectory,
    FixedClock,
    InMemorySentLog,
    InMemoryTaskRepository,
    OutboxMailer,
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


@pytest.fixture
def mailer() -> OutboxMailer:
    return OutboxMailer()


@pytest.fixture
def sent_log() -> InMemorySentLog:
    return InMemorySentLog()
