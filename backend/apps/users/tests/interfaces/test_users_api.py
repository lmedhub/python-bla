from datetime import timedelta

import pytest
from rest_framework_simplejwt.tokens import AccessToken

from apps.users.tests.factories import make_user

pytestmark = pytest.mark.django_db

USERS = "/api/v1/users"
ME = "/api/v1/users/me"


class TestListUsers:
    def test_lists_active_users_by_name_without_private_fields(self, login_as):
        bob = make_user(name="Bob", email="bob@example.com")
        alice = make_user(name="Alice", email="alice@example.com")
        make_user(name="Carol", is_active=False)

        response = login_as(bob).get(USERS)

        assert response.status_code == 200
        assert response.json() == [
            {"id": alice.pk, "email": "alice@example.com", "name": "Alice"},
            {"id": bob.pk, "email": "bob@example.com", "name": "Bob"},
        ]


class TestMe:
    def test_returns_the_current_user(self, login_as):
        alice = make_user(name="Alice", email="alice@example.com")

        response = login_as(alice).get(ME)

        assert response.status_code == 200
        assert response.json() == {"id": alice.pk, "email": "alice@example.com", "name": "Alice"}


class TestBearerToken:
    def test_no_token_is_401_with_a_bearer_challenge(self, api_client):
        response = api_client.get(ME)

        assert response.status_code == 401
        assert response.json()["code"] == "not_authenticated"
        assert response["WWW-Authenticate"].startswith("Bearer")

    def test_an_expired_token_is_401(self, api_client):
        token = AccessToken.for_user(make_user())
        token.set_exp(lifetime=-timedelta(seconds=1))
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        assert api_client.get(ME).status_code == 401

    def test_a_tampered_token_is_401(self, api_client):
        token = str(AccessToken.for_user(make_user()))
        tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tampered}")

        assert api_client.get(ME).status_code == 401

    def test_a_wrong_scheme_is_401(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {AccessToken.for_user(make_user())}")

        assert api_client.get(ME).status_code == 401

    def test_the_token_of_a_deactivated_user_is_401(self, login_as):
        user = make_user()
        client = login_as(user)
        user.is_active = False
        user.save()

        assert client.get(ME).status_code == 401

    def test_the_token_of_a_deleted_user_is_401(self, login_as):
        user = make_user()
        client = login_as(user)
        user.delete()

        assert client.get(ME).status_code == 401
