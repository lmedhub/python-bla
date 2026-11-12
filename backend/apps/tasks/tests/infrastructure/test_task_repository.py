from datetime import UTC, date, datetime, timedelta

import pytest

from apps.core.domain.errors import ConflictError
from apps.tasks.domain.task import Task, TaskStatus
from apps.tasks.infrastructure.repositories import DjangoTaskRepository
from apps.tasks.tests.fakes import FixedClock
from apps.users.tests.factories import make_user

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 11, 12, 9, 30, tzinfo=UTC)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)


@pytest.fixture
def repository(clock) -> DjangoTaskRepository:
    return DjangoTaskRepository(clock=clock)


@pytest.fixture
def creator_id() -> int:
    return int(make_user().pk)


def new_task(creator_id: int, **fields) -> Task:
    return Task(**{"title": "Write tests", "created_by_id": creator_id, **fields})


def test_add_returns_the_saved_task_with_id_version_and_timestamps(repository, creator_id):
    saved = repository.add(new_task(creator_id))

    assert saved.id is not None
    assert saved.version == 1
    assert saved.created_at == saved.updated_at == NOW


def test_get_round_trips_every_field(repository, creator_id):
    assignee_id = make_user().pk
    saved = repository.add(
        new_task(
            creator_id,
            description="All of them",
            status=TaskStatus.DONE,
            completed_at=NOW - timedelta(hours=1),
            due_date=date(2026, 12, 1),
            assignee_id=assignee_id,
        )
    )

    assert repository.get(saved.require_id()) == saved


def test_get_unknown_task_returns_none(repository):
    assert repository.get(999_999) is None


def test_update_saves_changes_bumps_the_version_and_the_update_time(repository, creator_id, clock):
    saved = repository.add(new_task(creator_id))
    clock.advance(timedelta(hours=1))
    saved.title = "Write more tests"

    updated = repository.update(saved)

    assert updated.version == 2
    assert updated.updated_at == NOW + timedelta(hours=1)
    assert updated.created_at == NOW
    assert repository.get(saved.require_id()) == updated


def test_concurrent_update_loses_with_a_conflict_and_the_first_write_is_kept(
    repository, creator_id
):
    saved = repository.add(new_task(creator_id))
    first_copy = repository.get(saved.require_id())
    second_copy = repository.get(saved.require_id())

    first_copy.title = "First writer"
    repository.update(first_copy)
    second_copy.title = "Second writer"

    with pytest.raises(ConflictError):
        repository.update(second_copy)

    assert repository.get(saved.require_id()).title == "First writer"


def test_update_of_a_deleted_task_is_a_conflict(repository, creator_id):
    saved = repository.add(new_task(creator_id))
    repository.delete(saved.require_id())

    with pytest.raises(ConflictError):
        repository.update(saved)


def test_delete_removes_the_task(repository, creator_id):
    saved = repository.add(new_task(creator_id))

    repository.delete(saved.require_id())

    assert repository.get(saved.require_id()) is None


def test_deleting_an_unknown_task_does_nothing(repository):
    repository.delete(999_999)
