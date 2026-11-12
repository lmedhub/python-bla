"""The database enforces the domain invariants too, so raw writes cannot break them."""

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.tasks.infrastructure import models
from apps.tasks.tests.factories import COMPLETED_AT, make_task_row
from apps.users.tests.factories import make_user

pytestmark = pytest.mark.django_db


def test_rejects_an_unknown_status():
    with pytest.raises(IntegrityError), transaction.atomic():
        make_task_row(status="archived")


def test_rejects_done_without_completed_at():
    with pytest.raises(IntegrityError), transaction.atomic():
        make_task_row(status="done", completed_at=None)


def test_rejects_completed_at_on_a_task_that_is_not_done():
    with pytest.raises(IntegrityError), transaction.atomic():
        make_task_row(status="in_progress", completed_at=COMPLETED_AT)


def test_rejects_an_empty_title():
    with pytest.raises(IntegrityError), transaction.atomic():
        make_task_row(title="")


def test_deleting_the_assignee_unassigns_their_tasks():
    assignee = make_user()
    row = make_task_row(assignee=assignee)

    assignee.delete()

    row.refresh_from_db()
    assert row.assignee_id is None


def test_a_user_who_created_tasks_cannot_be_deleted():
    # Users are deactivated, never deleted, so task history keeps its author.
    creator = make_user()
    make_task_row(created_by=creator)

    with pytest.raises(ProtectedError):
        creator.delete()


def test_has_an_index_on_status_and_due_date():
    index_fields = [index.fields for index in models.Task._meta.indexes]

    assert ["status", "due_date"] in index_fields


def test_shows_as_its_title():
    assert str(make_task_row(title="Write tests")) == "Write tests"
