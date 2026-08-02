"""Integration tests exercising the column management HTTP endpoints end-to-end."""

from __future__ import annotations

from httpx import AsyncClient

from tests.factories.board_factory import build_board_creation_request_payload
from tests.factories.column_factory import build_column_creation_request_payload


async def _create_board_and_return_its_identifier(
    authenticated_test_client: AsyncClient, board_title: str = "Column Test Board"
) -> str:
    """Create a board owned by the authenticated client and return its identifier."""
    response = await authenticated_test_client.post(
        "/api/v1/boards", json=build_board_creation_request_payload(board_title=board_title)
    )
    return str(response.json()["board_identifier"])


class TestCreateAndListColumnEndpoints:
    """Behavior of POST/GET /api/v1/boards/{board_identifier}/columns."""

    async def test_columns_are_appended_in_creation_order(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        board_identifier = await _create_board_and_return_its_identifier(authenticated_test_client)

        await authenticated_test_client.post(
            f"/api/v1/boards/{board_identifier}/columns",
            json=build_column_creation_request_payload(column_title="To Do"),
        )
        await authenticated_test_client.post(
            f"/api/v1/boards/{board_identifier}/columns",
            json=build_column_creation_request_payload(column_title="Done"),
        )

        response = await authenticated_test_client.get(f"/api/v1/boards/{board_identifier}/columns")

        assert response.status_code == 200
        response_columns = response.json()
        assert [column["column_title"] for column in response_columns] == ["To Do", "Done"]
        assert [column["column_display_order"] for column in response_columns] == [0, 1]

    async def test_returns_404_when_the_parent_board_does_not_exist(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        response = await authenticated_test_client.post(
            "/api/v1/boards/60c72b2f9b1e8b3f1c8e4d99/columns",
            json=build_column_creation_request_payload(),
        )

        assert response.status_code == 404


class TestColumnOwnershipIsEnforced:
    """A user must not be able to create, read, update, or delete columns on a board they do not
    own."""

    async def test_another_user_cannot_list_columns_for_a_board_they_do_not_own(
        self, test_http_client: AsyncClient, authenticated_test_client: AsyncClient
    ) -> None:
        board_identifier = await _create_board_and_return_its_identifier(authenticated_test_client)

        intruder_registration = {
            "email_address": "column.intruder@example.com",
            "plain_text_password": "correct-horse-battery-staple",
            "display_name": "Intruder",
        }
        await test_http_client.post("/api/v1/auth/register", json=intruder_registration)
        login_response = await test_http_client.post(
            "/api/v1/auth/login",
            json={
                "email_address": intruder_registration["email_address"],
                "plain_text_password": intruder_registration["plain_text_password"],
            },
        )
        test_http_client.headers["Authorization"] = (
            f"Bearer {login_response.json()['access_token_value']}"
        )

        response = await test_http_client.get(f"/api/v1/boards/{board_identifier}/columns")

        assert response.status_code == 403


class TestUpdateAndDeleteColumnEndpoints:
    """Behavior of PUT and DELETE /api/v1/columns/{column_identifier}."""

    async def test_update_column_persists_the_new_title(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        board_identifier = await _create_board_and_return_its_identifier(authenticated_test_client)
        create_response = await authenticated_test_client.post(
            f"/api/v1/boards/{board_identifier}/columns",
            json=build_column_creation_request_payload(column_title="Old Title"),
        )
        column_identifier = create_response.json()["column_identifier"]

        update_response = await authenticated_test_client.put(
            f"/api/v1/columns/{column_identifier}",
            json=build_column_creation_request_payload(column_title="New Title"),
        )

        assert update_response.status_code == 200
        assert update_response.json()["column_title"] == "New Title"

    async def test_delete_column_removes_it_from_the_board(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        board_identifier = await _create_board_and_return_its_identifier(authenticated_test_client)
        create_response = await authenticated_test_client.post(
            f"/api/v1/boards/{board_identifier}/columns",
            json=build_column_creation_request_payload(),
        )
        column_identifier = create_response.json()["column_identifier"]

        delete_response = await authenticated_test_client.delete(
            f"/api/v1/columns/{column_identifier}"
        )
        list_response = await authenticated_test_client.get(
            f"/api/v1/boards/{board_identifier}/columns"
        )

        assert delete_response.status_code == 204
        assert list_response.json() == []


class TestReorderColumnsEndpoint:
    """Behavior of PUT /api/v1/boards/{board_identifier}/columns/reorder."""

    async def _create_board_with_columns(
        self, authenticated_test_client: AsyncClient, column_titles: list[str]
    ) -> tuple[str, list[str]]:
        """Create a board with the given columns, returning (board_identifier, column_ids)."""
        board_identifier = await self._create_board(authenticated_test_client)
        column_identifiers = []
        for column_title in column_titles:
            response = await authenticated_test_client.post(
                f"/api/v1/boards/{board_identifier}/columns",
                json=build_column_creation_request_payload(column_title=column_title),
            )
            column_identifiers.append(str(response.json()["column_identifier"]))
        return board_identifier, column_identifiers

    async def _create_board(self, authenticated_test_client: AsyncClient) -> str:
        return await _create_board_and_return_its_identifier(authenticated_test_client)

    async def test_reorder_persists_across_a_fresh_read(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        board_identifier, column_identifiers = await self._create_board_with_columns(
            authenticated_test_client, ["To Do", "Doing", "Done"]
        )
        reversed_identifiers = list(reversed(column_identifiers))

        reorder_response = await authenticated_test_client.put(
            f"/api/v1/boards/{board_identifier}/columns/reorder",
            json={"ordered_column_identifiers": reversed_identifiers},
        )
        list_response = await authenticated_test_client.get(
            f"/api/v1/boards/{board_identifier}/columns"
        )

        assert reorder_response.status_code == 200
        assert [
            column["column_identifier"] for column in reorder_response.json()
        ] == reversed_identifiers
        assert [
            column["column_identifier"] for column in list_response.json()
        ] == reversed_identifiers
        assert [column["column_display_order"] for column in list_response.json()] == [0, 1, 2]

    async def test_returns_404_when_the_reorder_list_omits_a_column(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        board_identifier, column_identifiers = await self._create_board_with_columns(
            authenticated_test_client, ["To Do", "Doing"]
        )

        response = await authenticated_test_client.put(
            f"/api/v1/boards/{board_identifier}/columns/reorder",
            json={"ordered_column_identifiers": [column_identifiers[0]]},
        )

        assert response.status_code == 404

    async def test_returns_403_when_a_non_owner_attempts_to_reorder(
        self, test_http_client: AsyncClient, authenticated_test_client: AsyncClient
    ) -> None:
        board_identifier, column_identifiers = await self._create_board_with_columns(
            authenticated_test_client, ["To Do", "Doing"]
        )

        intruder_registration = {
            "email_address": "reorder.intruder@example.com",
            "plain_text_password": "correct-horse-battery-staple",
            "display_name": "Intruder",
        }
        await test_http_client.post("/api/v1/auth/register", json=intruder_registration)
        login_response = await test_http_client.post(
            "/api/v1/auth/login",
            json={
                "email_address": intruder_registration["email_address"],
                "plain_text_password": intruder_registration["plain_text_password"],
            },
        )
        test_http_client.headers["Authorization"] = (
            f"Bearer {login_response.json()['access_token_value']}"
        )

        response = await test_http_client.put(
            f"/api/v1/boards/{board_identifier}/columns/reorder",
            json={"ordered_column_identifiers": list(reversed(column_identifiers))},
        )

        assert response.status_code == 403
