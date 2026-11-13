from apps.tasks.application.ports import Clock
from apps.tasks.infrastructure.models import SentNotification


class DjangoSentLog:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def was_sent(self, key: str) -> bool:
        return SentNotification.objects.filter(key=key).exists()

    def record(self, key: str) -> None:
        # get_or_create, not create: a redelivered job racing the first one must not crash
        # on the unique key after its email already went out.
        SentNotification.objects.get_or_create(key=key, defaults={"sent_at": self._clock.now()})
