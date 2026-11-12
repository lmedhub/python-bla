from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

Probe = Callable[[], bool]
HealthStatus = Literal["ok", "degraded", "down"]


@dataclass(frozen=True)
class HealthReport:
    database: bool
    redis: bool

    @property
    def status(self) -> HealthStatus:
        if not self.database:
            return "down"
        # Redis only carries throttling and background jobs, so the API still works without it.
        if not self.redis:
            return "degraded"
        return "ok"


def check_health(*, database: Probe, redis: Probe) -> HealthReport:
    return HealthReport(database=database(), redis=redis())
