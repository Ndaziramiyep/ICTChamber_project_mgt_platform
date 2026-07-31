"""Integration tests exercising the authentication HTTP endpoints end-to-end."""

from __future__ import annotations

from httpx import AsyncClient

from tests.factories.user_factory import build_user_registration_request_payload


class TestRegisterEndpoint:
    """Behavior of POST /api/v1/auth/register."""

    async def test_returns_201_and_the_created_profile_for_a_new_email_address(
        self, test_http_client: AsyncClient
    ) -> None:
        registration_payload = build_user_registration_request_payload(
            email_address="fresh.signup@example.com"
        )

        response = await test_http_client.post("/api/v1/auth/register", json=registration_payload)

        assert response.status_code == 201
        response_body = response.json()
        assert response_body["email_address"] == "fresh.signup@example.com"
        assert "hashed_password_value" not in response_body

    async def test_returns_409_for_an_already_registered_email_address(
        self, test_http_client: AsyncClient
    ) -> None:
        registration_payload = build_user_registration_request_payload(
            email_address="duplicate.signup@example.com"
        )
        await test_http_client.post("/api/v1/auth/register", json=registration_payload)

        response = await test_http_client.post("/api/v1/auth/register", json=registration_payload)

        assert response.status_code == 409
        assert response.json()["error_code"] == "EmailAddressAlreadyRegisteredError"

    async def test_returns_422_for_a_password_shorter_than_the_minimum_length(
        self, test_http_client: AsyncClient
    ) -> None:
        registration_payload = build_user_registration_request_payload(
            email_address="short.password@example.com", plain_text_password="short"
        )

        response = await test_http_client.post("/api/v1/auth/register", json=registration_payload)

        assert response.status_code == 422


class TestLoginEndpoint:
    """Behavior of POST /api/v1/auth/login."""

    async def test_returns_a_token_pair_for_correct_credentials(
        self, test_http_client: AsyncClient
    ) -> None:
        registration_payload = build_user_registration_request_payload(
            email_address="login.success@example.com"
        )
        await test_http_client.post("/api/v1/auth/register", json=registration_payload)

        response = await test_http_client.post(
            "/api/v1/auth/login",
            json={
                "email_address": registration_payload["email_address"],
                "plain_text_password": registration_payload["plain_text_password"],
            },
        )

        assert response.status_code == 200
        response_body = response.json()
        assert response_body["access_token_value"]
        assert response_body["refresh_token_value"]

    async def test_returns_401_for_an_incorrect_password(
        self, test_http_client: AsyncClient
    ) -> None:
        registration_payload = build_user_registration_request_payload(
            email_address="login.wrong.password@example.com"
        )
        await test_http_client.post("/api/v1/auth/register", json=registration_payload)

        response = await test_http_client.post(
            "/api/v1/auth/login",
            json={
                "email_address": registration_payload["email_address"],
                "plain_text_password": "not-the-right-password",
            },
        )

        assert response.status_code == 401


class TestRefreshEndpoint:
    """Behavior of POST /api/v1/auth/refresh."""

    async def test_returns_a_new_access_token_for_a_valid_refresh_token(
        self, test_http_client: AsyncClient
    ) -> None:
        registration_payload = build_user_registration_request_payload(
            email_address="refresh.success@example.com"
        )
        await test_http_client.post("/api/v1/auth/register", json=registration_payload)
        login_response = await test_http_client.post(
            "/api/v1/auth/login",
            json={
                "email_address": registration_payload["email_address"],
                "plain_text_password": registration_payload["plain_text_password"],
            },
        )
        refresh_token_value = login_response.json()["refresh_token_value"]

        response = await test_http_client.post(
            "/api/v1/auth/refresh", json={"refresh_token_value": refresh_token_value}
        )

        assert response.status_code == 200
        assert response.json()["access_token_value"]

    async def test_returns_401_for_an_access_token_used_as_a_refresh_token(
        self, test_http_client: AsyncClient
    ) -> None:
        registration_payload = build_user_registration_request_payload(
            email_address="refresh.wrong.token.type@example.com"
        )
        await test_http_client.post("/api/v1/auth/register", json=registration_payload)
        login_response = await test_http_client.post(
            "/api/v1/auth/login",
            json={
                "email_address": registration_payload["email_address"],
                "plain_text_password": registration_payload["plain_text_password"],
            },
        )
        access_token_value = login_response.json()["access_token_value"]

        response = await test_http_client.post(
            "/api/v1/auth/refresh", json={"refresh_token_value": access_token_value}
        )

        assert response.status_code == 401


class TestGetAuthenticatedUserProfileEndpoint:
    """Behavior of GET /api/v1/auth/me."""

    async def test_returns_the_authenticated_users_profile(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        response = await authenticated_test_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        assert response.json()["email_address"] == "authenticated.client@example.com"

    async def test_returns_401_when_no_bearer_token_is_provided(
        self, test_http_client: AsyncClient
    ) -> None:
        response = await test_http_client.get("/api/v1/auth/me")

        assert response.status_code in (401, 403)
