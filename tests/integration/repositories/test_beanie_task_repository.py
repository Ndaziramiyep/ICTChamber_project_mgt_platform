"""Integration tests for BeanieTaskRepository against a real MongoDB test database."""

from __future__ import annotations

from app.infrastructure.persistence.repositories.beanie_task_repository import (
    BeanieTaskRepository,
)
from tests.factories.task_factory import build_kanban_task_entity


class TestCreateAndFindTaskRecord:
    """Persistence round-trip behavior for task records."""

    async def test_create_task_record_populates_a_generated_identifier(self) -> None:
        beanie_task_repository = BeanieTaskRepository()
        task_entity_to_persist = build_kanban_task_entity(task_identifier="")

        persisted_task_entity = await beanie_task_repository.create_task_record(
            task_entity_to_persist
        )

        assert persisted_task_entity.task_identifier

    async def test_find_tasks_by_parent_column_identifier_returns_them_ordered_by_position(
        self,
    ) -> None:
        beanie_task_repository = BeanieTaskRepository()
        await beanie_task_repository.create_task_record(
            build_kanban_task_entity(
                task_identifier="",
                parent_column_identifier="column-x",
                task_title="Third",
                task_position_value=3000.0,
            )
        )
        await beanie_task_repository.create_task_record(
            build_kanban_task_entity(
                task_identifier="",
                parent_column_identifier="column-x",
                task_title="First",
                task_position_value=1000.0,
            )
        )
        await beanie_task_repository.create_task_record(
            build_kanban_task_entity(
                task_identifier="",
                parent_column_identifier="column-x",
                task_title="Second",
                task_position_value=2000.0,
            )
        )

        ordered_tasks = await beanie_task_repository.find_tasks_by_parent_column_identifier(
            "column-x"
        )

        assert [task.task_title for task in ordered_tasks] == ["First", "Second", "Third"]

    async def test_find_highest_task_position_value_in_column_returns_none_when_empty(
        self,
    ) -> None:
        beanie_task_repository = BeanieTaskRepository()

        highest_position_value = (
            await beanie_task_repository.find_highest_task_position_value_in_column("empty-column")
        )

        assert highest_position_value is None

    async def test_find_highest_task_position_value_in_column_returns_the_maximum(self) -> None:
        beanie_task_repository = BeanieTaskRepository()
        await beanie_task_repository.create_task_record(
            build_kanban_task_entity(
                task_identifier="",
                parent_column_identifier="column-y",
                task_position_value=1000.0,
            )
        )
        await beanie_task_repository.create_task_record(
            build_kanban_task_entity(
                task_identifier="",
                parent_column_identifier="column-y",
                task_position_value=2500.0,
            )
        )

        highest_position_value = (
            await beanie_task_repository.find_highest_task_position_value_in_column("column-y")
        )

        assert highest_position_value == 2500.0

    async def test_update_task_record_persists_the_new_title(self) -> None:
        beanie_task_repository = BeanieTaskRepository()
        persisted_task_entity = await beanie_task_repository.create_task_record(
            build_kanban_task_entity(task_identifier="", task_title="Old Title")
        )
        persisted_task_entity.task_title = "New Title"

        updated_task_entity = await beanie_task_repository.update_task_record(persisted_task_entity)

        assert updated_task_entity.task_title == "New Title"

    async def test_delete_task_by_identifier_removes_the_record(self) -> None:
        beanie_task_repository = BeanieTaskRepository()
        persisted_task_entity = await beanie_task_repository.create_task_record(
            build_kanban_task_entity(task_identifier="")
        )

        await beanie_task_repository.delete_task_by_identifier(
            persisted_task_entity.task_identifier
        )

        assert (
            await beanie_task_repository.find_task_by_identifier(
                persisted_task_entity.task_identifier
            )
            is None
        )

    async def test_delete_tasks_by_parent_column_identifier_removes_all_of_them(self) -> None:
        beanie_task_repository = BeanieTaskRepository()
        await beanie_task_repository.create_task_record(
            build_kanban_task_entity(task_identifier="", parent_column_identifier="column-z")
        )
        await beanie_task_repository.create_task_record(
            build_kanban_task_entity(task_identifier="", parent_column_identifier="column-z")
        )

        await beanie_task_repository.delete_tasks_by_parent_column_identifier("column-z")

        assert await beanie_task_repository.find_tasks_by_parent_column_identifier("column-z") == []

    async def test_delete_tasks_by_parent_board_identifier_removes_tasks_across_all_its_columns(
        self,
    ) -> None:
        beanie_task_repository = BeanieTaskRepository()
        await beanie_task_repository.create_task_record(
            build_kanban_task_entity(
                task_identifier="",
                parent_column_identifier="column-in-board-w-1",
                parent_board_identifier="board-w",
            )
        )
        await beanie_task_repository.create_task_record(
            build_kanban_task_entity(
                task_identifier="",
                parent_column_identifier="column-in-board-w-2",
                parent_board_identifier="board-w",
            )
        )
        await beanie_task_repository.create_task_record(
            build_kanban_task_entity(
                task_identifier="",
                parent_column_identifier="column-in-other-board",
                parent_board_identifier="board-other",
            )
        )

        await beanie_task_repository.delete_tasks_by_parent_board_identifier("board-w")

        assert (
            await beanie_task_repository.find_tasks_by_parent_column_identifier(
                "column-in-board-w-1"
            )
            == []
        )
        assert (
            await beanie_task_repository.find_tasks_by_parent_column_identifier(
                "column-in-board-w-2"
            )
            == []
        )
        assert (
            len(
                await beanie_task_repository.find_tasks_by_parent_column_identifier(
                    "column-in-other-board"
                )
            )
            == 1
        )
