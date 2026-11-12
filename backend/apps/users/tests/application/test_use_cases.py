import pytest

from apps.core.domain.errors import NotFoundError
from apps.users.application.use_cases import GetUser, ListActiveUsers
from apps.users.domain.user import User

ALICE = User(id=1, email="alice@example.com", name="Alice")
BOB = User(id=2, email="bob@example.com", name="Bob")
CAROL = User(id=3, email="carol@example.com", name="Carol", is_active=False)


class InMemoryUserRepository:
    def __init__(self, users: list[User]) -> None:
        self.rows = {user.id: user for user in users}

    def get(self, user_id: int) -> User | None:
        return self.rows.get(user_id)

    def list_active(self) -> list[User]:
        return [user for user in self.rows.values() if user.is_active]


@pytest.fixture
def users() -> InMemoryUserRepository:
    return InMemoryUserRepository([ALICE, BOB, CAROL])


def test_new_users_are_active_by_default():
    assert ALICE.is_active is True


class TestListActiveUsers:
    def test_returns_what_the_repository_lists(self, users):
        assert ListActiveUsers(users=users).execute() == [ALICE, BOB]


class TestGetUser:
    def test_returns_the_user(self, users):
        assert GetUser(users=users).execute(BOB.id) == BOB

    def test_inactive_users_can_still_be_read(self, users):
        # The current user endpoint must work for any authenticated user;
        # deactivation is enforced at login, not here.
        assert GetUser(users=users).execute(CAROL.id) == CAROL

    def test_unknown_user_is_not_found(self, users):
        with pytest.raises(NotFoundError):
            GetUser(users=users).execute(999)
