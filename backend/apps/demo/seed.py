"""Demo users and tasks, written straight to the database.

Not through the use cases on purpose: they refuse a due date in the past (which overdue demo
tasks need) and would email every assignee.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SeedResult:
    users: int
    tasks: int


def seed_demo(*, password: str, now: datetime) -> SeedResult | None:
    """Seeds an empty database. Returns None, and changes nothing, if any user exists."""
    raise NotImplementedError
