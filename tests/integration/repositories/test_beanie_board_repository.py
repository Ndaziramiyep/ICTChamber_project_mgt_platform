"""Integration tests for BeanieBoardRepository against a real MongoDB test database."""

from __future__ import annotations

from app.infrastructure.persistence.repositories.beanie_board_repository import (
    BeanieBoardRepository,
)
from tests.factories.board_factory import build_project_board_entity


class TestCreateAndFindBoardRecord:
    """Persistence round-trip behavior for board records."""

    async def test_create_board_record_populates_a_generated_identifier(self) -> None:
        beanie_board_repository = BeanieBoardRepository()
        board_entity_to_persist = build_project_board_entity(board_identifier="")

        persisted_board_entity = await beanie_board_repository.create_board_record(
            board_entity_to_persist
        )

        assert persisted_board_entity.board_identifier

    async def test_find_boards_owned_by_user_identifier_returns_only_that_users_boards(
        self,
    ) -> None:
        beanie_board_repository = BeanieBoardRepository()
        await beanie_board_repository.create_board_record(
            build_project_board_entity(board_identifier="", owning_user_identifier="user-a")
        )
        await beanie_board_repository.create_board_record(
            build_project_board_entity(board_identifier="", owning_user_identifier="user-a")
        )
        await beanie_board_repository.create_board_record(
            build_project_board_entity(board_identifier="", owning_user_identifier="user-b")
        )

        user_a_boards = await beanie_board_repository.find_boards_owned_by_user_identifier("user-a")

        assert len(user_a_boards) == 2
        assert all(board.owning_user_identifier == "user-a" for board in user_a_boards)

    async def test_update_board_record_persists_the_new_title(self) -> None:
        beanie_board_repository = BeanieBoardRepository()
        persisted_board_entity = await beanie_board_repository.create_board_record(
            build_project_board_entity(board_identifier="", board_title="Original Title")
        )
        persisted_board_entity.board_title = "Renamed Title"

        updated_board_entity = await beanie_board_repository.update_board_record(
            persisted_board_entity
        )

        assert updated_board_entity.board_title == "Renamed Title"
        refetched_board_entity = await beanie_board_repository.find_board_by_identifier(
            persisted_board_entity.board_identifier
        )
        assert refetched_board_entity is not None
        assert refetched_board_entity.board_title == "Renamed Title"

    async def test_delete_board_by_identifier_removes_the_record(self) -> None:
        beanie_board_repository = BeanieBoardRepository()
        persisted_board_entity = await beanie_board_repository.create_board_record(
            build_project_board_entity(board_identifier="")
        )

        await beanie_board_repository.delete_board_by_identifier(
            persisted_board_entity.board_identifier
        )

        assert (
            await beanie_board_repository.find_board_by_identifier(
                persisted_board_entity.board_identifier
            )
            is None
        )

    async def test_find_board_by_identifier_returns_none_for_an_invalid_identifier(self) -> None:
        beanie_board_repository = BeanieBoardRepository()

        found_board_entity = await beanie_board_repository.find_board_by_identifier("not-an-id")

        assert found_board_entity is None
