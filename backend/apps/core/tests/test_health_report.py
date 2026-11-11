import pytest

from apps.core.application.health import check_health


def up() -> bool:
    return True


def down() -> bool:
    return False


@pytest.mark.parametrize(
    ("database", "redis", "expected"),
    [
        (up, up, "ok"),
        # The app still serves requests without Redis, so this is not an outage.
        (up, down, "degraded"),
        (down, up, "down"),
        (down, down, "down"),
    ],
)
def test_status_depends_on_which_dependency_is_down(database, redis, expected):
    report = check_health(database=database, redis=redis)

    assert report.status == expected


def test_report_keeps_each_probe_result():
    report = check_health(database=up, redis=down)

    assert report.database is True
    assert report.redis is False
