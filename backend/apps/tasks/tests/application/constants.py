from datetime import UTC, datetime

CREATOR = 1
ASSIGNEE = 2
STRANGER = 3
# Exists but is not active, so FakeUserDirectory does not list it.
INACTIVE_USER = 4
UNKNOWN_USER = 999

NOW = datetime(2026, 11, 12, 9, 30, tzinfo=UTC)
