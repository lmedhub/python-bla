from datetime import date, datetime

from django.utils import timezone


class SystemClock:
    """The real clock. With USE_TZ=True, timezone.now() is an aware UTC datetime."""

    def now(self) -> datetime:
        return timezone.now()

    def today(self) -> date:
        return self.now().date()
