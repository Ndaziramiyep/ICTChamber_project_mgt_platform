"""Integration tests for BeanieColumnRepository against a real MongoDB test database."""

from __future__ import annotations

from app.infrastructure.persistence.repositories.beanie_column_repository import (
    BeanieColumnRepository,
)
from tests.factories.column_factory import build_board_column_entity


class TestCreateAndFindColumnRecord:
    """Persistence round-trip behavior for column records."""

    async def test_create_column_record_populates_a_generated_identifier(self) -> None:
        beanie_column_repository = BeanieColumnRepository()
        column_entity_to_persist = build_board_column_entity(column_identifier="")

        persisted_column_entity = await beanie_column_repository.create_column_record(
            column_entity_to_persist
        )

        assert persisted_column_entity.column_identifier

    async def test_find_columns_by_parent_board_identifier_returns_them_in_display_order(
        self,
    ) -> None:
        beanie_column_repository = BeanieColumnRepository()
        await beanie_column_repository.create_column_record(
            build_board_column_entity(
                column_identifier="",
                parent_board_identifier="board-x",
                column_title="Done",
                column_display_order=2,
            )
        )
        await beanie_column_repository.create_column_record(
            build_board_column_entity(
                column_identifier="",
                parent_board_identifier="board-x",
                column_title="To Do",
                column_display_order=0,
            )
        )
        await beanie_column_repository.create_column_record(
            build_board_column_entity(
                column_identifier="",
                parent_board_identifier="board-x",
                column_title="In Progress",
                column_display_order=1,
            )
        )

        ordered_columns = await beanie_column_repository.find_columns_by_parent_board_identifier(
            "board-x"
        )

        assert [column.column_title for column in ordered_columns] == [
            "To Do",
            "In Progress",
            "Done",
        ]

    async def test_update_column_record_persists_the_new_title(self) -> None:
        beanie_column_repository = BeanieColumnRepository()
        persisted_column_entity = await beanie_column_repository.create_column_record(
            build_board_column_entity(column_identifier="", column_title="Old Title")
        )
        persisted_column_entity.column_title = "New Title"

        updated_column_entity = await beanie_column_repository.update_column_record(
            persisted_column_entity
        )

        assert updated_column_entity.column_title == "New Title"

    async def test_delete_column_by_identifier_removes_the_record(self) -> None:
        beanie_column_repository = BeanieColumnRepository()
        persisted_column_entity = await beanie_column_repository.create_column_record(
            build_board_column_entity(column_identifier="")
        )

        await beanie_column_repository.delete_column_by_identifier(
            persisted_column_entity.column_identifier
        )

        assert (
            await beanie_column_repository.find_column_by_identifier(
                persisted_column_entity.column_identifier
            )
            is None
        )

    async def test_delete_columns_by_parent_board_identifier_removes_all_of_them(self) -> None:
        beanie_column_repository = BeanieColumnRepository()
        await beanie_column_repository.create_column_record(
            build_board_column_entity(column_identifier="", parent_board_identifier="board-y")
        )
        await beanie_column_repository.create_column_record(
            build_board_column_entity(column_identifier="", parent_board_identifier="board-y")
        )

        await beanie_column_repository.delete_columns_by_parent_board_identifier("board-y")

        assert (
            await beanie_column_repository.find_columns_by_parent_board_identifier("board-y") == []
        )
