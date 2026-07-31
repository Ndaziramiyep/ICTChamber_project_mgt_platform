"""Fixtures for exercising the real FastAPI application end-to-end over real HTTP semantics."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from pymongo import AsyncMongoClient

from app.core.application_settings import ApplicationSettings
from app.main import create_fastapi_application
from tests.factories.user_factory import build_user_registration_request_payload


@pytest.fixture
async def test_http_client(
    test_application_settings: ApplicationSettings,
    real_test_mongo_client: AsyncMongoClient,
) -> AsyncIterator[AsyncClient]:
    """Return an httpx.AsyncClient bound to the real FastAPI application via ASGI transport.

    The application's own startup/shutdown lifespan (which opens and closes its own MongoDB
    client) is deliberately NOT triggered here. Beanie document models are already initialized
    against the test database for the whole test session by real_test_mongo_client; running the
    application's lifespan on top of that would open a second client and close it when this
    function-scoped fixture tears down, severing the document models from the session's
    connection for every test that runs afterwards.
    """
    del real_test_mongo_client
    test_fastapi_application = create_fastapi_application(
        application_settings=test_application_settings
    )

    transport = ASGITransport(app=test_fastapi_application)
    async with AsyncClient(transport=transport, base_url="http://test-server") as http_client:
        yield http_client


@pytest.fixture
async def authenticated_test_client(test_http_client: AsyncClient) -> AsyncClient:
    """Register and log in a throwaway user, returning a client pre-loaded with a bearer token."""
    registration_payload = build_user_registration_request_payload(
        email_address="authenticated.client@example.com"
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
    test_http_client.headers["Authorization"] = f"Bearer {access_token_value}"

    return test_http_client
