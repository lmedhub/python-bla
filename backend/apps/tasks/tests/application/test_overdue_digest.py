from datetime import date, timedelta

import pytest

from apps.tasks.application.notifications import SendOverdueDigests
from apps.tasks.domain.task import Task, TaskStatus
from apps.tasks.tests.application.constants import ASSIGNEE, CREATOR, INACTIVE_USER, NOW, STRANGER
from apps.tasks.tests.fakes import BrokenMailer, InMemoryTaskRepository

TODAY = NOW.date()
YESTERDAY = TODAY - timedelta(days=1)
LAST_WEEK = TODAY - timedelta(days=7)


@pytest.fixture
def digest(tasks, users, mailer, sent_log, clock) -> SendOverdueDigests:
    return SendOverdueDigests(
        tasks=tasks, users=users, mailer=mailer, sent_log=sent_log, clock=clock
    )


def add(
    tasks: InMemoryTaskRepository,
    title: str,
    assignee_id: int | None = ASSIGNEE,
    due_date: date | None = YESTERDAY,
    status: TaskStatus = TaskStatus.TODO,
) -> Task:
    return tasks.add(
        Task(
            title=title,
            created_by_id=CREATOR,
            assignee_id=assignee_id,
            due_date=due_date,
            status=status,
        )
    )


def test_sends_each_assignee_one_email_listing_their_overdue_tasks(digest, tasks, mailer):
    add(tasks, "Pay invoices", due_date=YESTERDAY)
    add(tasks, "Renew domain", due_date=LAST_WEEK)
    add(tasks, "Book flights", assignee_id=STRANGER)

    sent = digest.execute()

    assert sent == 2
    by_recipient = {email.to: email for email in mailer.outbox}
    mine = by_recipient["user2@example.com"]
    assert mine.subject == "You have 2 overdue tasks"
    # Oldest first: the most overdue task is at the top.
    assert mine.body.index("Renew domain (due 2026-11-05)") < mine.body.index(
        "Pay invoices (due 2026-11-11)"
    )
    assert by_recipient["user3@example.com"].subject == "You have 1 overdue task"


def test_ignores_tasks_that_are_not_overdue(digest, tasks, mailer):
    add(tasks, "Due today", due_date=TODAY)
    add(tasks, "No due date", due_date=None)
    add(tasks, "Already done", status=TaskStatus.DONE)

    assert digest.execute() == 0
    assert mailer.outbox == []


def test_overdue_tasks_without_an_assignee_email_nobody(digest, tasks, mailer):
    add(tasks, "Nobody's job", assignee_id=None)

    assert digest.execute() == 0
    assert mailer.outbox == []


def test_skips_inactive_assignees(digest, tasks, mailer):
    add(tasks, "Left the company", assignee_id=INACTIVE_USER)

    assert digest.execute() == 0
    assert mailer.outbox == []


def test_running_twice_on_the_same_day_sends_nothing_new(digest, tasks, mailer):
    # Beat may fire twice, or the job may be retried after a partial failure.
    add(tasks, "Pay invoices")

    digest.execute()
    assert digest.execute() == 0

    assert len(mailer.outbox) == 1


def test_the_next_day_sends_again(digest, tasks, mailer, clock):
    add(tasks, "Pay invoices")

    digest.execute()
    clock.advance(timedelta(days=1))
    digest.execute()

    assert len(mailer.outbox) == 2


def test_a_failed_send_is_not_recorded(tasks, users, sent_log, clock, mailer):
    add(tasks, "Pay invoices")
    failing = SendOverdueDigests(
        tasks=tasks, users=users, mailer=BrokenMailer(), sent_log=sent_log, clock=clock
    )

    with pytest.raises(ConnectionRefusedError):
        failing.execute()

    retry = SendOverdueDigests(
        tasks=tasks, users=users, mailer=mailer, sent_log=sent_log, clock=clock
    )
    assert retry.execute() == 1
