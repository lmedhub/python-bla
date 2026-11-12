from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    email: str
    name: str
    is_active: bool = True


def normalize_email(raw: str) -> str:
    raise NotImplementedError
