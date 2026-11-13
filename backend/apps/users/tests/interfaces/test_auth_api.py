from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db

LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
COOKIE = "refresh_token"
PASSWORD = "correct horse battery staple"


@pytest.fixture
def alice():
    return get_user_model().objects.create_user(
        email="alice@example.com", password=PASSWORD, name="Alice"
    )


def login(client, email="alice@example.com", password=PASSWORD):
    return client.post(LOGIN, {"email": email, "password": password}, format="json")


class TestLogin:
    def test_returns_an_access_token_and_the_user(self, api_client, alice):
        response = login(api_client)

        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"access", "user"}
        assert body["user"] == {"id": alice.pk, "email": "alice@example.com", "name": "Alice"}

    def test_puts_the_refresh_token_only_in_a_locked_down_cookie(self, api_client, alice):
        response = login(api_client)

        assert "refresh" not in response.json()
        cookie = response.cookies[COOKIE]
        assert cookie.value
        assert cookie["httponly"] is True
        assert cookie["samesite"] == "Strict"
        assert cookie["path"] == "/api/v1/auth"
        assert cookie["secure"] is True
        assert cookie["max-age"] == int(timedelta(days=1).total_seconds())

    def test_email_is_case_insensitive(self, api_client, alice):
        assert login(api_client, email="ALICE@Example.com").status_code == 200

    @pytest.mark.parametrize(
        ("email", "password"),
        [("alice@example.com", "wrong password"), ("nobody@example.com", PASSWORD)],
    )
    def test_bad_credentials_get_the_same_401(self, api_client, alice, email, password):
        response = login(api_client, email=email, password=password)

        assert response.status_code == 401
        assert response.json() == {
            "code": "not_authenticated",
            "detail": "Invalid email or password.",
            "fields": {},
        }
        assert response["WWW-Authenticate"].startswith("Bearer")
        assert COOKIE not in response.cookies

    def test_inactive_users_get_the_same_401(self, api_client, alice):
        alice.is_active = False
        alice.save()

        response = login(api_client)

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password."

    def test_missing_fields_are_400(self, api_client):
        response = api_client.post(LOGIN, {}, format="json")

        assert response.status_code == 400
        assert set(response.json()["fields"]) == {"email", "password"}

    def test_a_stale_bearer_header_does_not_block_login(self, api_client, alice):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")

        assert login(api_client).status_code == 200


class TestRefresh:
    def test_rotates_the_cookie_and_returns_a_new_session(self, api_client, alice):
        old_cookie = login(api_client).cookies[COOKIE].value

        response = api_client.post(REFRESH)

        assert response.status_code == 200
        assert set(response.json()) == {"access", "user"}
        assert response.json()["user"]["id"] == alice.pk
        assert response.cookies[COOKIE].value != old_cookie

    def test_an_already_used_refresh_token_is_rejected(self, api_client, alice):
        old_cookie = login(api_client).cookies[COOKIE].value
        api_client.post(REFRESH)
        api_client.cookies[COOKIE] = old_cookie

        response = api_client.post(REFRESH)

        assert response.status_code == 401
        assert response.json()["code"] == "not_authenticated"

    def test_no_cookie_is_401(self, api_client):
        response = api_client.post(REFRESH)

        assert response.status_code == 401
        assert response["WWW-Authenticate"].startswith("Bearer")

    def test_a_tampered_token_is_401(self, api_client, alice):
        token = login(api_client).cookies[COOKIE].value
        api_client.cookies[COOKIE] = token[:-2] + ("aa" if not token.endswith("aa") else "bb")

        assert api_client.post(REFRESH).status_code == 401

    def test_an_expired_token_is_401(self, api_client, alice):
        token = RefreshToken.for_user(alice)
        token.set_exp(lifetime=-timedelta(seconds=1))
        api_client.cookies[COOKIE] = str(token)

        assert api_client.post(REFRESH).status_code == 401

    def test_a_deactivated_user_cannot_refresh(self, api_client, alice):
        login(api_client)
        alice.is_active = False
        alice.save()

        assert api_client.post(REFRESH).status_code == 401

    def test_a_deleted_user_cannot_refresh_and_it_is_not_a_500(self, api_client, alice):
        # simplejwt 5.5.1 raises User.DoesNotExist here; the view must turn it into a 401.
        login(api_client)
        alice.delete()

        assert api_client.post(REFRESH).status_code == 401


class TestLogout:
    def test_clears_the_cookie_and_blacklists_the_token(self, api_client, alice):
        token = login(api_client).cookies[COOKIE].value

        response = api_client.post(LOGOUT)

        assert response.status_code == 204
        assert response.cookies[COOKIE].value == ""
        assert response.cookies[COOKIE]["max-age"] == 0
        api_client.cookies[COOKIE] = token
        assert api_client.post(REFRESH).status_code == 401

    def test_is_safe_without_a_cookie(self, api_client):
        assert api_client.post(LOGOUT).status_code == 204

    def test_is_safe_with_a_garbage_cookie(self, api_client):
        api_client.cookies[COOKIE] = "garbage"

        assert api_client.post(LOGOUT).status_code == 204
