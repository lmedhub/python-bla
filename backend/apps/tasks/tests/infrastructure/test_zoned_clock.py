from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from apps.tasks.infrastructure.clock import ZonedClock
from apps.tasks.tests.fakes import FixedClock

# 21:21 on the 12th in São Paulo is already the 13th in UTC: the case seen in the manual run.
LATE_EVENING_IN_BRAZIL = datetime(2026, 11, 13, 0, 21, tzinfo=UTC)
SAO_PAULO = ZoneInfo("America/Sao_Paulo")


def test_today_is_the_date_in_the_callers_zone():
    clock = ZonedClock(FixedClock(LATE_EVENING_IN_BRAZIL), SAO_PAULO)

    assert clock.today() == date(2026, 11, 12)


def test_in_utc_it_is_already_the_next_day():
    clock = ZonedClock(FixedClock(LATE_EVENING_IN_BRAZIL), UTC)

    assert clock.today() == date(2026, 11, 13)


def test_now_is_the_same_instant_whatever_the_zone():
    clock = ZonedClock(FixedClock(LATE_EVENING_IN_BRAZIL), SAO_PAULO)

    assert clock.now() == LATE_EVENING_IN_BRAZIL


def test_zones_east_of_utc_can_be_a_day_ahead():
    just_before_midnight_utc = datetime(2026, 11, 12, 23, 30, tzinfo=UTC)
    clock = ZonedClock(FixedClock(just_before_midnight_utc), ZoneInfo("Asia/Tokyo"))

    assert clock.today() == date(2026, 11, 13)
