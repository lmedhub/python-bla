from datetime import date, datetime


class SystemClock:
    def now(self) -> datetime:
        raise NotImplementedError

    def today(self) -> date:
        raise NotImplementedError
