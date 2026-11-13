from collections.abc import Collection

from django.contrib.auth import get_user_model

from apps.tasks.application.ports import Recipient


class DjangoUserDirectory:
    """Answers "is this an active user?" for tasks without importing the users feature.

    Django resolves the user model from AUTH_USER_MODEL, the same indirection the task
    foreign keys use, so tasks never imports users.infrastructure (ADR 0009).
    """

    def is_active_user(self, user_id: int) -> bool:
        return get_user_model().objects.filter(pk=user_id, is_active=True).exists()

    def active_recipients(self, user_ids: Collection[int]) -> dict[int, Recipient]:
        raise NotImplementedError
