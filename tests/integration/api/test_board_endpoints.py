"""Integration tests exercising the board management HTTP endpoints end-to-end."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from app.core.application_settings import ApplicationSettings
from app.main import create_fastapi_application
from tests.factories.board_factory import build_board_creation_request_payload
from tests.factories.user_factory import build_user_registration_request_payload


async def _register_and_authenticate_new_user(
    test_http_client: AsyncClient, email_address: str
) -> None:
    """Register a new user and set the resulting access token as the client's bearer header."""
    registration_payload = build_user_registration_request_payload(email_address=email_address)
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


class TestCreateBoardEndpoint:
    """Behavior of POST /api/v1/boards."""

    async def test_returns_201_and_the_created_board_owned_by_the_caller(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        response = await authenticated_test_client.post(
            "/api/v1/boards", json=build_board_creation_request_payload(board_title="Sprint Board")
        )

        assert response.status_code == 201
        assert response.json()["board_title"] == "Sprint Board"

    async def test_returns_401_when_no_bearer_token_is_provided(
        self, test_http_client: AsyncClient
    ) -> None:
        response = await test_http_client.post(
            "/api/v1/boards", json=build_board_creation_request_payload()
        )

        assert response.status_code in (401, 403)


class TestListAndGetBoardEndpoints:
    """Behavior of GET /api/v1/boards and GET /api/v1/boards/{board_identifier}."""

    async def test_list_boards_returns_only_the_callers_own_boards(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        await authenticated_test_client.post(
            "/api/v1/boards", json=build_board_creation_request_payload(board_title="Board One")
        )
        await authenticated_test_client.post(
            "/api/v1/boards", json=build_board_creation_request_payload(board_title="Board Two")
        )

        response = await authenticated_test_client.get("/api/v1/boards")

        assert response.status_code == 200
        response_board_titles = {board["board_title"] for board in response.json()}
        assert {"Board One", "Board Two"}.issubset(response_board_titles)

    async def test_get_board_returns_404_for_an_unknown_board_identifier(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        response = await authenticated_test_client.get("/api/v1/boards/60c72b2f9b1e8b3f1c8e4d99")

        assert response.status_code == 404


class TestBoardOwnershipIsEnforced:
    """A user must not be able to read, update, or delete another user's board."""

    async def test_another_user_receives_403_when_accessing_a_board_they_do_not_own(
        self, test_application_settings: ApplicationSettings
    ) -> None:
        test_fastapi_application = create_fastapi_application(
            application_settings=test_application_settings
        )
        transport = ASGITransport(app=test_fastapi_application)

        async with AsyncClient(transport=transport, base_url="http://test-server") as owner_client:
            await _register_and_authenticate_new_user(owner_client, "board.owner@example.com")
            create_response = await owner_client.post(
                "/api/v1/boards", json=build_board_creation_request_payload()
            )
            owned_board_identifier = create_response.json()["board_identifier"]

        async with AsyncClient(
            transport=transport, base_url="http://test-server"
        ) as intruder_client:
            await _register_and_authenticate_new_user(intruder_client, "board.intruder@example.com")

            get_response = await intruder_client.get(f"/api/v1/boards/{owned_board_identifier}")
            update_response = await intruder_client.put(
                f"/api/v1/boards/{owned_board_identifier}",
                json=build_board_creation_request_payload(board_title="Hijacked"),
            )
            delete_response = await intruder_client.delete(
                f"/api/v1/boards/{owned_board_identifier}"
            )

        assert get_response.status_code == 403
        assert update_response.status_code == 403
        assert delete_response.status_code == 403


class TestUpdateAndDeleteBoardEndpoints:
    """Behavior of PUT and DELETE /api/v1/boards/{board_identifier} for the owning user."""

    async def test_update_board_persists_the_new_title(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        create_response = await authenticated_test_client.post(
            "/api/v1/boards", json=build_board_creation_request_payload(board_title="Old Title")
        )
        board_identifier = create_response.json()["board_identifier"]

        update_response = await authenticated_test_client.put(
            f"/api/v1/boards/{board_identifier}",
            json=build_board_creation_request_payload(board_title="New Title"),
        )

        assert update_response.status_code == 200
        assert update_response.json()["board_title"] == "New Title"

    async def test_delete_board_removes_it_from_the_list(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        create_response = await authenticated_test_client.post(
            "/api/v1/boards", json=build_board_creation_request_payload()
        )
        board_identifier = create_response.json()["board_identifier"]

        delete_response = await authenticated_test_client.delete(
            f"/api/v1/boards/{board_identifier}"
        )
        get_response = await authenticated_test_client.get(f"/api/v1/boards/{board_identifier}")

        assert delete_response.status_code == 204
        assert get_response.status_code == 404
