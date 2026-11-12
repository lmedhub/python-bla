from apps.core.domain.errors import NotFoundError
from apps.users.application.ports import UserRepository
from apps.users.domain.user import User


class ListActiveUsers:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def execute(self) -> list[User]:
        return self._users.list_active()


class GetUser:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def execute(self, user_id: int) -> User:
        user = self._users.get(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return user
