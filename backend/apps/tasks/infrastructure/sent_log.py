from apps.tasks.application.ports import Clock


class DjangoSentLog:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def was_sent(self, key: str) -> bool:
        raise NotImplementedError

    def record(self, key: str) -> None:
        raise NotImplementedError
