from typing import Protocol

from apps.users.domain.user import User


class UserRepository(Protocol):
    def get(self, user_id: int) -> User | None: ...

    def list_active(self) -> list[User]: ...
