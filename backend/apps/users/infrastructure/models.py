from typing import ClassVar

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower

from apps.users.domain.user import normalize_email


class UserManager(BaseUserManager["User"]):
    def create_user(
        self, email: str, password: str | None = None, *, name: str, is_active: bool = True
    ) -> "User":
        user = self.model(email=normalize_email(email), name=name, is_active=is_active)
        user.set_password(password)  # None gives an unusable password
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, username: str | None) -> "User":
        # Login looks users up here, so "Alice@Example.com" finds "alice@example.com".
        return self.get(email=normalize_email(username or ""))


class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)

    objects: ClassVar[UserManager] = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = ["name"]

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            # Emails are stored lowercase, so the plain unique index is also case-insensitive.
            models.CheckConstraint(
                condition=models.Q(email=Lower("email")), name="users_user_email_lowercase"
            ),
        ]

    def __str__(self) -> str:
        return self.email
