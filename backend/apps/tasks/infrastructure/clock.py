from datetime import date, datetime, tzinfo

from apps.tasks.application.ports import Clock


class ZonedClock:
    def __init__(self, clock: Clock, zone: tzinfo) -> None:
        self._clock = clock
        self._zone = zone

    def now(self) -> datetime:
        raise NotImplementedError

    def today(self) -> date:
        raise NotImplementedError
