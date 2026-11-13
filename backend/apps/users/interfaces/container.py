"""Composition root for users: the only interfaces module allowed to import infrastructure."""

from apps.users.application.use_cases import GetUser, ListActiveUsers
from apps.users.infrastructure.repositories import DjangoUserRepository


def get_user() -> GetUser:
    return GetUser(users=DjangoUserRepository())


def list_active_users() -> ListActiveUsers:
    return ListActiveUsers(users=DjangoUserRepository())
