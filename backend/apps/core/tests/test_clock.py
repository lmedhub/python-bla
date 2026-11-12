from datetime import UTC, date, datetime, timedelta

from apps.core.infrastructure.clock import SystemClock


def test_now_is_timezone_aware_utc():
    now = SystemClock().now()

    assert now.utcoffset() == timedelta(0)


class _LateEvening(SystemClock):
    def now(self) -> datetime:
        return datetime(2026, 11, 12, 23, 59, tzinfo=UTC)


def test_today_is_the_date_of_now_in_utc():
    assert _LateEvening().today() == date(2026, 11, 12)
