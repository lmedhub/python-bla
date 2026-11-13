"""Rate limits: anonymous 20/min, signed in 100/min, login 5/min per client IP (ADR 0005)."""

import logging

import pytest

from apps.users.tests.factories import make_user

pytestmark = pytest.mark.django_db

LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
ME = "/api/v1/users/me"
TASKS = "/api/v1/tasks"
WRONG_LOGIN = {"email": "nobody@example.com", "password": "wrong"}


def test_the_sixth_login_attempt_in_a_minute_is_429(api_client):
    statuses = [api_client.post(LOGIN, WRONG_LOGIN, format="json").status_code for _ in range(6)]

    assert statuses == [401] * 5 + [429]


def test_a_429_says_when_to_retry_in_the_shared_error_shape(api_client):
    for _ in range(5):
        api_client.post(LOGIN, WRONG_LOGIN, format="json")

    response = api_client.post(LOGIN, WRONG_LOGIN, format="json")

    assert response.json()["code"] == "throttled"
    assert int(response["Retry-After"]) > 0


def test_behind_a_proxy_each_client_ip_gets_its_own_login_limit(api_client, settings):
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "NUM_PROXIES": 1}
    for _ in range(5):
        api_client.post(LOGIN, WRONG_LOGIN, format="json", HTTP_X_FORWARDED_FOR="203.0.113.1")

    other_client = api_client.post(
        LOGIN, WRONG_LOGIN, format="json", HTTP_X_FORWARDED_FOR="203.0.113.2"
    )

    assert other_client.status_code == 401


def test_anonymous_callers_get_20_requests_a_minute(api_client):
    statuses = [api_client.post(REFRESH).status_code for _ in range(21)]

    assert statuses == [401] * 20 + [429]


def test_signed_in_users_get_100_requests_a_minute(login_as):
    client = login_as(make_user())

    statuses = [client.get(ME).status_code for _ in range(101)]

    assert statuses == [200] * 100 + [429]


class TestRedisDown:
    @pytest.fixture
    def redis_down(self, settings):
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": "redis://localhost:1/0",
                "OPTIONS": {"socket_connect_timeout": 1, "socket_timeout": 1},
            }
        }

    def test_login_still_works_and_a_warning_is_logged(self, api_client, redis_down, caplog):
        user = make_user(email="dora@example.com")
        user.set_password("pw-for-redis-test")
        user.save()

        with caplog.at_level(logging.WARNING):
            response = api_client.post(
                LOGIN, {"email": "dora@example.com", "password": "pw-for-redis-test"}, format="json"
            )

        assert response.status_code == 200
        assert "Rate limiting skipped" in caplog.text

    def test_the_task_list_still_works(self, login_as, redis_down):
        assert login_as(make_user()).get(TASKS).status_code == 200
