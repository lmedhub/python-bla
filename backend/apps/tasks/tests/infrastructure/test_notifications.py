import logging

from apps.tasks.infrastructure.notifications import LoggingNotifier


def test_logs_who_was_assigned_which_task(caplog):
    with caplog.at_level(logging.INFO, logger="apps.tasks.infrastructure.notifications"):
        LoggingNotifier().task_assigned(task_id=7, assignee_id=3)

    assert "Task 7 was assigned to user 3." in caplog.text
