from datetime import date, datetime, tzinfo

from apps.tasks.application.ports import Clock


class ZonedClock:
    """A clock whose "today" is the caller's date (ADR 0007).

    now() is an instant and has no zone, so it passes through unchanged. Only the calendar
    date depends on where the caller is: 21:21 in Sao Paulo is already tomorrow in UTC.
    """

    def __init__(self, clock: Clock, zone: tzinfo) -> None:
        self._clock = clock
        self._zone = zone

    def now(self) -> datetime:
        return self._clock.now()

    def today(self) -> date:
        return self._clock.now().astimezone(self._zone).date()
