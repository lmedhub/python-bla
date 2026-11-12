import pytest

from apps.users.domain.user import normalize_email


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("alice@example.com", "alice@example.com"),
        ("Alice@Example.COM", "alice@example.com"),
        ("  bob@example.com \n", "bob@example.com"),
    ],
)
def test_emails_are_trimmed_and_lowercased(raw: str, expected: str):
    assert normalize_email(raw) == expected
