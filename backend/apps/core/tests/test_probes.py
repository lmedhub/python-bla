import pytest

from apps.core.infrastructure.probes import database_is_up, redis_is_up

# Nothing listens on port 1, so the connection is refused at once.
UNREACHABLE_REDIS = "redis://localhost:1/0"


@pytest.mark.django_db
def test_database_probe_is_up_against_real_postgres():
    assert database_is_up() is True


def test_redis_probe_is_up_against_real_redis():
    assert redis_is_up() is True


def test_redis_probe_reports_down_when_unreachable(settings):
    settings.REDIS_URL = UNREACHABLE_REDIS

    assert redis_is_up() is False
