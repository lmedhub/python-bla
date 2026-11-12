from apps.users.domain.user import User
from apps.users.infrastructure import models


class DjangoUserRepository:
    def get(self, user_id: int) -> User | None:
        row = models.User.objects.filter(pk=user_id).first()
        return _to_entity(row) if row else None

    def list_active(self) -> list[User]:
        rows = models.User.objects.filter(is_active=True).order_by("name", "id")
        return [_to_entity(row) for row in rows]


def _to_entity(row: models.User) -> User:
    return User(id=row.pk, email=row.email, name=row.name, is_active=row.is_active)
