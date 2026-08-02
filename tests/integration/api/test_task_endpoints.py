"""Integration tests exercising the task management HTTP endpoints end-to-end."""

from __future__ import annotations

from httpx import AsyncClient

from tests.factories.board_factory import build_board_creation_request_payload
from tests.factories.column_factory import build_column_creation_request_payload
from tests.factories.task_factory import build_task_creation_request_payload


async def _create_board_and_column_and_return_identifiers(
    authenticated_test_client: AsyncClient,
) -> tuple[str, str]:
    """Create a board and a column within it, returning (board_identifier, column_identifier)."""
    board_response = await authenticated_test_client.post(
        "/api/v1/boards", json=build_board_creation_request_payload(board_title="Task Test Board")
    )
    board_identifier = str(board_response.json()["board_identifier"])

    column_response = await authenticated_test_client.post(
        f"/api/v1/boards/{board_identifier}/columns",
        json=build_column_creation_request_payload(column_title="To Do"),
    )
    column_identifier = str(column_response.json()["column_identifier"])

    return board_identifier, column_identifier


class TestCreateAndListTaskEndpoints:
    """Behavior of POST/GET /api/v1/columns/{column_identifier}/tasks."""

    async def test_tasks_are_appended_in_increasing_position_order(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        _, column_identifier = await _create_board_and_column_and_return_identifiers(
            authenticated_test_client
        )

        await authenticated_test_client.post(
            f"/api/v1/columns/{column_identifier}/tasks",
            json=build_task_creation_request_payload(task_title="First task"),
        )
        await authenticated_test_client.post(
            f"/api/v1/columns/{column_identifier}/tasks",
            json=build_task_creation_request_payload(task_title="Second task"),
        )

        response = await authenticated_test_client.get(f"/api/v1/columns/{column_identifier}/tasks")

        assert response.status_code == 200
        response_tasks = response.json()
        assert [task["task_title"] for task in response_tasks] == ["First task", "Second task"]
        assert response_tasks[0]["task_position_value"] < response_tasks[1]["task_position_value"]

    async def test_created_task_carries_the_boards_denormalized_identifier(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        board_identifier, column_identifier = await _create_board_and_column_and_return_identifiers(
            authenticated_test_client
        )

        response = await authenticated_test_client.post(
            f"/api/v1/columns/{column_identifier}/tasks",
            json=build_task_creation_request_payload(),
        )

        assert response.json()["parent_board_identifier"] == board_identifier

    async def test_returns_404_when_the_parent_column_does_not_exist(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        response = await authenticated_test_client.post(
            "/api/v1/columns/60c72b2f9b1e8b3f1c8e4d99/tasks",
            json=build_task_creation_request_payload(),
        )

        assert response.status_code == 404


class TestTaskOwnershipIsEnforced:
    """A user must not be able to create or list tasks for a column on a board they do not own."""

    async def test_another_user_cannot_list_tasks_for_a_column_they_do_not_own(
        self, test_http_client: AsyncClient, authenticated_test_client: AsyncClient
    ) -> None:
        _, column_identifier = await _create_board_and_column_and_return_identifiers(
            authenticated_test_client
        )

        intruder_registration = {
            "email_address": "task.intruder@example.com",
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

        response = await test_http_client.get(f"/api/v1/columns/{column_identifier}/tasks")

        assert response.status_code == 403


class TestUpdateAndDeleteTaskEndpoints:
    """Behavior of PUT and DELETE /api/v1/tasks/{task_identifier}."""

    async def test_update_task_persists_the_new_title_and_description(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        _, column_identifier = await _create_board_and_column_and_return_identifiers(
            authenticated_test_client
        )
        create_response = await authenticated_test_client.post(
            f"/api/v1/columns/{column_identifier}/tasks",
            json=build_task_creation_request_payload(task_title="Old Title"),
        )
        task_identifier = create_response.json()["task_identifier"]

        update_response = await authenticated_test_client.put(
            f"/api/v1/tasks/{task_identifier}",
            json=build_task_creation_request_payload(
                task_title="New Title", task_description="New description"
            ),
        )

        assert update_response.status_code == 200
        assert update_response.json()["task_title"] == "New Title"
        assert update_response.json()["task_description"] == "New description"

    async def test_delete_task_removes_it_from_the_column(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        _, column_identifier = await _create_board_and_column_and_return_identifiers(
            authenticated_test_client
        )
        create_response = await authenticated_test_client.post(
            f"/api/v1/columns/{column_identifier}/tasks",
            json=build_task_creation_request_payload(),
        )
        task_identifier = create_response.json()["task_identifier"]

        delete_response = await authenticated_test_client.delete(f"/api/v1/tasks/{task_identifier}")
        list_response = await authenticated_test_client.get(
            f"/api/v1/columns/{column_identifier}/tasks"
        )

        assert delete_response.status_code == 204
        assert list_response.json() == []


class TestRepositionTaskEndpoint:
    """Behavior of PATCH /api/v1/tasks/{task_identifier}/position."""

    async def test_reposition_persists_the_new_order_within_the_same_column(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        _, column_identifier = await _create_board_and_column_and_return_identifiers(
            authenticated_test_client
        )
        task_identifiers = []
        for task_title in ["A", "B", "C"]:
            response = await authenticated_test_client.post(
                f"/api/v1/columns/{column_identifier}/tasks",
                json=build_task_creation_request_payload(task_title=task_title),
            )
            task_identifiers.append(str(response.json()["task_identifier"]))
        task_a, _, task_c = task_identifiers

        reposition_response = await authenticated_test_client.patch(
            f"/api/v1/tasks/{task_c}/position",
            json={
                "target_column_identifier": column_identifier,
                "previous_task_identifier": None,
                "next_task_identifier": task_a,
            },
        )
        list_response = await authenticated_test_client.get(
            f"/api/v1/columns/{column_identifier}/tasks"
        )

        assert reposition_response.status_code == 200
        assert [task["task_title"] for task in list_response.json()] == ["C", "A", "B"]

    async def test_reposition_moves_a_task_to_a_different_column(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        board_identifier, source_column_identifier = (
            await _create_board_and_column_and_return_identifiers(authenticated_test_client)
        )
        target_column_response = await authenticated_test_client.post(
            f"/api/v1/boards/{board_identifier}/columns",
            json=build_column_creation_request_payload(column_title="Done"),
        )
        target_column_identifier = str(target_column_response.json()["column_identifier"])
        create_response = await authenticated_test_client.post(
            f"/api/v1/columns/{source_column_identifier}/tasks",
            json=build_task_creation_request_payload(task_title="Move me"),
        )
        task_identifier = create_response.json()["task_identifier"]

        reposition_response = await authenticated_test_client.patch(
            f"/api/v1/tasks/{task_identifier}/position",
            json={"target_column_identifier": target_column_identifier},
        )
        source_list_response = await authenticated_test_client.get(
            f"/api/v1/columns/{source_column_identifier}/tasks"
        )
        target_list_response = await authenticated_test_client.get(
            f"/api/v1/columns/{target_column_identifier}/tasks"
        )

        assert reposition_response.status_code == 200
        assert reposition_response.json()["parent_column_identifier"] == target_column_identifier
        assert source_list_response.json() == []
        assert [task["task_title"] for task in target_list_response.json()] == ["Move me"]

    async def test_returns_404_when_previous_task_identifier_is_not_in_the_target_column(
        self, authenticated_test_client: AsyncClient
    ) -> None:
        _, column_identifier = await _create_board_and_column_and_return_identifiers(
            authenticated_test_client
        )
        create_response = await authenticated_test_client.post(
            f"/api/v1/columns/{column_identifier}/tasks",
            json=build_task_creation_request_payload(),
        )
        task_identifier = create_response.json()["task_identifier"]

        response = await authenticated_test_client.patch(
            f"/api/v1/tasks/{task_identifier}/position",
            json={
                "target_column_identifier": column_identifier,
                "previous_task_identifier": "60c72b2f9b1e8b3f1c8e4d99",
            },
        )

        assert response.status_code == 404

    async def test_returns_403_when_the_target_column_belongs_to_another_users_board(
        self, test_http_client: AsyncClient, authenticated_test_client: AsyncClient
    ) -> None:
        _, column_identifier = await _create_board_and_column_and_return_identifiers(
            authenticated_test_client
        )
        create_response = await authenticated_test_client.post(
            f"/api/v1/columns/{column_identifier}/tasks",
            json=build_task_creation_request_payload(),
        )
        task_identifier = create_response.json()["task_identifier"]

        intruder_registration = {
            "email_address": "position.intruder@example.com",
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
        intruders_board_response = await test_http_client.post(
            "/api/v1/boards",
            json=build_board_creation_request_payload(board_title="Intruder board"),
        )
        intruders_board_identifier = str(intruders_board_response.json()["board_identifier"])
        intruders_column_response = await test_http_client.post(
            f"/api/v1/boards/{intruders_board_identifier}/columns",
            json=build_column_creation_request_payload(column_title="Intruder column"),
        )
        intruders_column_identifier = str(intruders_column_response.json()["column_identifier"])

        response = await authenticated_test_client.patch(
            f"/api/v1/tasks/{task_identifier}/position",
            json={"target_column_identifier": intruders_column_identifier},
        )

        assert response.status_code == 403
