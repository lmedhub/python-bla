from apps.users.domain.user import User


class DjangoUserRepository:
    def get(self, user_id: int) -> User | None:
        raise NotImplementedError

    def list_active(self) -> list[User]:
        raise NotImplementedError
