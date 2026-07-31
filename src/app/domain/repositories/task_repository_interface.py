"""Abstract persistence contract for Kanban tasks."""

from __future__ import annotations

from typing import Protocol

from app.domain.entities.kanban_task_entity import KanbanTaskEntity


class TaskRepositoryInterface(Protocol):
    """Persistence operations required by the task management and reordering use cases."""

    async def create_task_record(
        self, task_entity_to_persist: KanbanTaskEntity
    ) -> KanbanTaskEntity:
        """Persist a new task record and return it as stored."""
        ...

    async def find_task_by_identifier(self, task_identifier: str) -> KanbanTaskEntity | None:
        """Return the task with the given identifier, or None if no such task exists."""
        ...

    async def find_tasks_by_parent_column_identifier(
        self, parent_column_identifier: str
    ) -> list[KanbanTaskEntity]:
        """Return every task in the given column, ordered ascending by task_position_value."""
        ...

    async def find_highest_task_position_value_in_column(
        self, parent_column_identifier: str
    ) -> float | None:
        """Return the highest task_position_value in the given column, or None if it is empty."""
        ...

    async def update_task_record(
        self, task_entity_to_persist: KanbanTaskEntity
    ) -> KanbanTaskEntity:
        """Persist changes to an existing task record and return it as stored."""
        ...

    async def delete_task_by_identifier(self, task_identifier: str) -> None:
        """Delete the task with the given identifier."""
        ...

    async def delete_tasks_by_parent_column_identifier(self, parent_column_identifier: str) -> None:
        """Delete every task belonging to the given column."""
        ...

    async def delete_tasks_by_parent_board_identifier(self, parent_board_identifier: str) -> None:
        """Delete every task belonging to the given board, across all of its columns."""
        ...
