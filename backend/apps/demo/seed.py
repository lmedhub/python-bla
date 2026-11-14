"""Demo users and tasks, written straight to the database.

Not through the use cases on purpose: they refuse a due date in the past (which overdue demo
tasks need) and would email every assignee.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.tasks.domain.task import TaskStatus
from apps.tasks.infrastructure.models import Task


@dataclass(frozen=True)
class SeedResult:
    users: int
    tasks: int


USERS = (
    ("alice@example.com", "Alice"),
    ("bob@example.com", "Bob"),
    ("carol@example.com", "Carol"),
    ("dana@example.com", "Dana"),
)

TODO, DOING, DONE = TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE

# (title, creator, assignee, status, due in days from today; None means no due date).
# Negative days and not done: overdue. Covers every status, overdue, due today, unassigned,
# no due date, done in the past, and every user as both creator and assignee.
TASKS: tuple[tuple[str, str, str | None, TaskStatus, int | None], ...] = (
    ("Prepare Q4 budget review", "Alice", "Bob", DOING, -3),
    ("Renew SSL certificates", "Alice", "Carol", TODO, -6),
    ("Update onboarding checklist", "Bob", None, TODO, -2),
    ("Fix login rate limit alert", "Carol", "Alice", TODO, -1),
    ("Book venue for team offsite", "Dana", "Dana", DOING, 0),
    ("Review pull request #42", "Bob", "Alice", TODO, 0),
    ("Write release notes for v1.4", "Alice", "Alice", TODO, 2),
    ("Migrate CI to new runners", "Carol", "Bob", DOING, 5),
    ("Plan sprint 24", "Dana", "Bob", TODO, 7),
    ("Customer interview: Acme Corp", "Alice", "Dana", TODO, 3),
    ("Archive old chat channels", "Bob", None, TODO, None),
    ("Research error tracking tools", "Carol", None, TODO, 14),
    ("Refresh dashboard screenshots", "Dana", "Carol", TODO, None),
    ("Draft hiring plan for 2027", "Alice", "Bob", TODO, 21),
    ("Clean up feature flags", "Bob", "Carol", DOING, 10),
    ("Order new laptops", "Dana", "Alice", TODO, -4),
    ("Set up staging database backups", "Carol", "Dana", TODO, 1),
    ("Send November invoices", "Alice", "Carol", DONE, -2),
    ("Publish security policy", "Bob", "Alice", DONE, -10),
    ("Run quarterly access review", "Carol", "Bob", DONE, 3),
    ("Organize the knowledge base", "Dana", None, DONE, None),
    ("Translate help center to Spanish", "Alice", "Dana", DOING, 12),
    ("Reply to partner questionnaire", "Bob", "Dana", TODO, -8),
    ("Test mobile layout at 320px", "Carol", "Alice", DONE, -1),
    ("Prepare demo for Thursday", "Dana", "Bob", TODO, 4),
    ("Rotate API keys", "Alice", None, TODO, 30),
    ("Update privacy notice", "Bob", "Bob", DOING, -1),
    ("Review vendor contract", "Carol", "Carol", TODO, None),
    ("Fix flaky checkout test", "Dana", "Alice", DOING, 2),
    ("Celebrate the launch", "Alice", None, TODO, 45),
)


@transaction.atomic
def seed_demo(*, password: str, now: datetime) -> SeedResult | None:
    """Seeds an empty database. Returns None, and changes nothing, if any user exists."""
    user_model = get_user_model()
    if user_model.objects.exists():
        return None

    users = {
        name: user_model.objects.create_user(email, password, name=name) for email, name in USERS
    }
    today = now.date()
    rows = [
        Task(
            title=title,
            created_by=users[creator],
            assignee=users[assignee] if assignee else None,
            status=status.value,
            due_date=None if due_in_days is None else today + timedelta(days=due_in_days),
            # The database requires completed_at exactly when the task is done.
            completed_at=now - timedelta(hours=3) if status is DONE else None,
            created_at=now - timedelta(days=14),
            updated_at=now,
        )
        for title, creator, assignee, status, due_in_days in TASKS
    ]
    Task.objects.bulk_create(rows)
    return SeedResult(users=len(users), tasks=len(rows))
