from datetime import UTC, datetime
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.demo.seed import seed_demo
from apps.tasks.domain.task import TaskStatus
from apps.tasks.infrastructure.models import Task
from apps.users.tests.factories import make_user

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 11, 14, 12, 0, tzinfo=UTC)
TODAY = NOW.date()
PASSWORD = "demo-password-for-tests"


@pytest.fixture
def seeded():
    result = seed_demo(password=PASSWORD, now=NOW)
    assert result is not None
    return result


def overdue_tasks():
    return Task.objects.filter(due_date__lt=TODAY).exclude(status=TaskStatus.DONE.value)


def test_creates_at_least_three_users_and_about_thirty_tasks(seeded):
    assert seeded.users == get_user_model().objects.count() >= 3
    assert seeded.tasks == Task.objects.count() >= 28


def test_covers_every_case_the_demo_needs(seeded):
    statuses = set(Task.objects.values_list("status", flat=True))
    assert statuses == {status.value for status in TaskStatus}
    assert overdue_tasks().count() >= 3
    assert overdue_tasks().filter(assignee__isnull=True).exists()
    assert Task.objects.filter(assignee__isnull=True).count() >= 2
    assert Task.objects.filter(due_date__isnull=True).count() >= 2
    assert Task.objects.filter(due_date=TODAY).exists()
    assert Task.objects.filter(due_date__gt=TODAY).exists()
    # Done and in the past: not overdue, and the badge must not show.
    assert Task.objects.filter(status=TaskStatus.DONE.value, due_date__lt=TODAY).exists()


def test_every_user_creates_and_is_assigned_tasks(seeded):
    for user in get_user_model().objects.all():
        assert Task.objects.filter(created_by=user).exists(), user
        assert Task.objects.filter(assignee=user).exists(), user


def test_done_tasks_have_a_completion_time_and_others_do_not(seeded):
    assert not Task.objects.filter(status=TaskStatus.DONE.value, completed_at__isnull=True).exists()
    assert (
        not Task.objects.exclude(status=TaskStatus.DONE.value)
        .filter(completed_at__isnull=False)
        .exists()
    )


def test_does_nothing_when_any_user_exists():
    make_user()

    assert seed_demo(password=PASSWORD, now=NOW) is None
    assert get_user_model().objects.count() == 1
    assert Task.objects.count() == 0


def test_demo_users_can_sign_in(seeded):
    response = APIClient().post(
        "/api/v1/auth/login",
        {"email": "alice@example.com", "password": PASSWORD},
        format="json",
    )

    assert response.status_code == 200


class TestCommand:
    def test_seeds_once_and_says_so(self, monkeypatch):
        monkeypatch.setenv("DEMO_PASSWORD", PASSWORD)
        first, second = StringIO(), StringIO()

        call_command("seed_demo", stdout=first)
        count = Task.objects.count()
        call_command("seed_demo", stdout=second)

        assert first.getvalue().startswith("Seeded 4 users and ")
        assert second.getvalue().strip() == "The database already has users; nothing seeded."
        assert Task.objects.count() == count

    def test_needs_the_demo_password(self, monkeypatch):
        monkeypatch.delenv("DEMO_PASSWORD", raising=False)

        with pytest.raises(ImproperlyConfigured, match="DEMO_PASSWORD"):
            call_command("seed_demo", stdout=StringIO())
