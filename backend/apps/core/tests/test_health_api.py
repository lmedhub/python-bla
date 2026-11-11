import pytest
from rest_framework.test import APIClient

from apps.core.application.health import HealthReport
from apps.core.interfaces import container

URL = "/api/v1/health"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_health_is_public_and_ok_when_everything_is_up(client):
    response = client.get(URL)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": "up", "redis": "up"}}


@pytest.mark.django_db
def test_health_is_degraded_but_200_when_redis_is_down(client, settings):
    settings.REDIS_URL = "redis://localhost:1/0"

    response = client.get(URL)

    assert response.status_code == 200
    assert response.json() == {"status": "degraded", "checks": {"database": "up", "redis": "down"}}


def test_health_is_503_when_database_is_down(client, monkeypatch):
    # No django_db mark: if the view opened a request transaction (ATOMIC_REQUESTS),
    # pytest-django would block the DB access and this test would fail.
    monkeypatch.setattr(
        container, "health_report", lambda: HealthReport(database=False, redis=True)
    )

    response = client.get(URL)

    assert response.status_code == 503
    assert response.json() == {"status": "down", "checks": {"database": "down", "redis": "up"}}


def test_health_rejects_writes(client):
    response = client.post(URL)

    assert response.status_code == 405
