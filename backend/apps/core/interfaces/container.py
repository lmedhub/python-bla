"""Composition root: the only interfaces module allowed to import infrastructure."""

from apps.core.application.health import HealthReport, check_health
from apps.core.infrastructure.probes import database_is_up, redis_is_up


def health_report() -> HealthReport:
    return check_health(database=database_is_up, redis=redis_is_up)
