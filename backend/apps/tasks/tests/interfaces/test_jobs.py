"""The Celery jobs, run in-process with .apply(): real database, Django's test outbox."""

import logging
from datetime import timedelta

import pytest

from apps.tasks.infrastructure.models import SentNotification
from apps.tasks.interfaces.jobs import notify_assignment, send_overdue_digests
from apps.tasks.tests.application.constants import NOW
from apps.tasks.tests.factories import make_task_row
from config.celery import app
from config.settings.base import overdue_digest_schedule, smtp_mailer

pytestmark = pytest.mark.django_db


def test_the_assignment_job_emails_the_assignee_and_logs_it(alice, bob, mailoutbox, caplog):
    task = make_task_row(title="Pay invoices", created_by=alice, assignee=bob)

    with caplog.at_level(logging.INFO, logger="apps.tasks.interfaces.jobs"):
        result = notify_assignment.apply(args=[task.pk, bob.pk])

    assert result.get() == "sent"
    [email] = mailoutbox
    assert email.to == ["bob@example.com"]
    assert email.subject == 'You were assigned "Pay invoices"'
    assert f"Assignment email for task {task.pk} to user {bob.pk}: sent." in caplog.text


def test_a_redelivered_assignment_job_sends_nothing_new(alice, bob, mailoutbox):
    task = make_task_row(created_by=alice, assignee=bob)

    notify_assignment.apply(args=[task.pk, bob.pk], task_id="same-message")
    again = notify_assignment.apply(args=[task.pk, bob.pk], task_id="same-message")

    assert again.get() == "already_sent"
    assert len(mailoutbox) == 1


def test_the_digest_job_emails_assignees_of_overdue_tasks(alice, bob, mailoutbox, caplog):
    # The interfaces conftest fixes the container clock at NOW.
    make_task_row(created_by=alice, assignee=bob, due_date=NOW.date() - timedelta(days=1))
    make_task_row(created_by=alice, assignee=alice, due_date=NOW.date())

    with caplog.at_level(logging.INFO, logger="apps.tasks.interfaces.jobs"):
        result = send_overdue_digests.apply()

    assert result.get() == 1
    assert [email.to for email in mailoutbox] == [["bob@example.com"]]
    assert "Overdue digest: 1 email(s) sent." in caplog.text


def test_the_beat_schedule_runs_a_registered_job():
    job_name = overdue_digest_schedule(schedule=None)["overdue-digest"]["task"]

    assert job_name == send_overdue_digests.name
    assert job_name in app.tasks


@pytest.mark.parametrize("job", [notify_assignment, send_overdue_digests])
def test_jobs_retry_mail_failures_with_growing_delays(job):
    assert job.autoretry_for == (OSError,)
    assert job.retry_backoff is True
    assert job.retry_jitter is True
    assert job.max_retries == 5


def test_an_unreachable_mail_server_fails_the_job_and_records_nothing(settings, alice, bob):
    settings.MAILERS = smtp_mailer(host="127.0.0.1", port=1)
    task = make_task_row(created_by=alice, assignee=bob)

    # Start at the last allowed attempt, so the failure is final instead of retried.
    result = notify_assignment.apply(args=[task.pk, bob.pk], retries=notify_assignment.max_retries)

    assert result.failed()
    assert isinstance(result.result, OSError)
    assert not SentNotification.objects.exists()
