from datetime import UTC, datetime

import pytest

from apps.tasks.infrastructure.models import SentNotification
from apps.tasks.infrastructure.sent_log import DjangoSentLog
from apps.tasks.tests.fakes import FixedClock

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 11, 12, 8, 0, tzinfo=UTC)


@pytest.fixture
def sent_log() -> DjangoSentLog:
    return DjangoSentLog(clock=FixedClock(NOW))


def test_a_recorded_key_was_sent(sent_log):
    assert sent_log.was_sent("digest:1:2026-11-12") is False

    sent_log.record("digest:1:2026-11-12")

    assert sent_log.was_sent("digest:1:2026-11-12") is True
    assert sent_log.was_sent("digest:1:2026-11-13") is False


def test_records_when_it_was_sent(sent_log):
    sent_log.record("assignment:abc")

    assert SentNotification.objects.get(key="assignment:abc").sent_at == NOW


def test_recording_the_same_key_twice_is_harmless(sent_log):
    # Two workers may race on a redelivered job; the second record must not crash it.
    sent_log.record("assignment:abc")
    sent_log.record("assignment:abc")

    assert SentNotification.objects.filter(key="assignment:abc").count() == 1
