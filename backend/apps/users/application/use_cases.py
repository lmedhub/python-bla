from apps.users.application.ports import UserRepository
from apps.users.domain.user import User


class ListActiveUsers:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def execute(self) -> list[User]:
        raise NotImplementedError


class GetUser:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def execute(self, user_id: int) -> User:
        raise NotImplementedError
