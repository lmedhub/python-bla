from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    email: str
    name: str
    is_active: bool = True


def normalize_email(raw: str) -> str:
    # Lowercase the whole address, not just the domain: "Alice@..." and "alice@..." should be
    # the same account. Mail servers almost never treat the local part as case-sensitive.
    return raw.strip().lower()
