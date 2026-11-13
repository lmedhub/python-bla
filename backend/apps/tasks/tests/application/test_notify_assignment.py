from datetime import date

import pytest

from apps.tasks.application.notifications import Delivery, NotifyAssignment
from apps.tasks.domain.task import Task
from apps.tasks.tests.application.constants import ASSIGNEE, CREATOR, INACTIVE_USER, STRANGER
from apps.tasks.tests.fakes import BrokenMailer, InMemoryTaskRepository

MESSAGE_ID = "3f1c0d9e-message"


@pytest.fixture
def notify(tasks, users, mailer, sent_log) -> NotifyAssignment:
    return NotifyAssignment(tasks=tasks, users=users, mailer=mailer, sent_log=sent_log)


def assigned_task(tasks: InMemoryTaskRepository, assignee_id=ASSIGNEE, **fields) -> Task:
    return tasks.add(
        Task(title="Write the report", created_by_id=CREATOR, assignee_id=assignee_id, **fields)
    )


def test_emails_the_assignee(notify, tasks, mailer):
    task = assigned_task(tasks, due_date=date(2026, 11, 20))

    delivery = notify.execute(task.require_id(), ASSIGNEE, MESSAGE_ID)

    assert delivery is Delivery.SENT
    [email] = mailer.outbox
    assert email.to == "user2@example.com"
    assert email.subject == 'You were assigned "Write the report"'
    assert "Hi User 2," in email.body
    assert "Due: 2026-11-20" in email.body


def test_says_when_there_is_no_due_date(notify, tasks, mailer):
    task = assigned_task(tasks)

    notify.execute(task.require_id(), ASSIGNEE, MESSAGE_ID)

    assert "Due: no due date" in mailer.outbox[0].body


def test_the_same_message_is_sent_only_once(notify, tasks, mailer):
    # A broker may deliver a job twice (acks_late, worker restart). The second run is a no-op.
    task = assigned_task(tasks)

    notify.execute(task.require_id(), ASSIGNEE, MESSAGE_ID)
    second = notify.execute(task.require_id(), ASSIGNEE, MESSAGE_ID)

    assert second is Delivery.ALREADY_SENT
    assert len(mailer.outbox) == 1


def test_a_new_assignment_is_a_new_message(notify, tasks, mailer):
    # Reassigned away and back: two assignments, two emails.
    task = assigned_task(tasks)

    notify.execute(task.require_id(), ASSIGNEE, "first-message")
    notify.execute(task.require_id(), ASSIGNEE, "second-message")

    assert len(mailer.outbox) == 2


def test_skips_a_task_deleted_before_the_job_ran(notify, mailer):
    assert notify.execute(404, ASSIGNEE, MESSAGE_ID) is Delivery.TASK_DELETED
    assert mailer.outbox == []


def test_skips_when_the_task_was_reassigned_before_the_job_ran(notify, tasks, mailer):
    # The payload says who *was* assigned; the stored task says who is assigned now.
    task = assigned_task(tasks, assignee_id=STRANGER)

    assert notify.execute(task.require_id(), ASSIGNEE, MESSAGE_ID) is Delivery.REASSIGNED
    assert mailer.outbox == []


def test_skips_an_assignee_deactivated_before_the_job_ran(notify, tasks, mailer):
    task = assigned_task(tasks, assignee_id=INACTIVE_USER)

    delivery = notify.execute(task.require_id(), INACTIVE_USER, MESSAGE_ID)

    assert delivery is Delivery.ASSIGNEE_INACTIVE
    assert mailer.outbox == []


def test_a_failed_send_is_not_recorded_so_the_retry_sends_it(tasks, users, sent_log, mailer):
    task = assigned_task(tasks)
    failing = NotifyAssignment(tasks=tasks, users=users, mailer=BrokenMailer(), sent_log=sent_log)

    with pytest.raises(ConnectionRefusedError):
        failing.execute(task.require_id(), ASSIGNEE, MESSAGE_ID)

    retry = NotifyAssignment(tasks=tasks, users=users, mailer=mailer, sent_log=sent_log)
    assert retry.execute(task.require_id(), ASSIGNEE, MESSAGE_ID) is Delivery.SENT
