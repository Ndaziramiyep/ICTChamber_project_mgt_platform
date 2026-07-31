"""Abstract persistence contract for board columns."""

from __future__ import annotations

from typing import Protocol

from app.domain.entities.board_column_entity import BoardColumnEntity


class ColumnRepositoryInterface(Protocol):
    """Persistence operations required by the column management use cases."""

    async def create_column_record(
        self, column_entity_to_persist: BoardColumnEntity
    ) -> BoardColumnEntity:
        """Persist a new column record and return it as stored."""
        ...

    async def find_column_by_identifier(self, column_identifier: str) -> BoardColumnEntity | None:
        """Return the column with the given identifier, or None if no such column exists."""
        ...

    async def find_columns_by_parent_board_identifier(
        self, parent_board_identifier: str
    ) -> list[BoardColumnEntity]:
        """Return every column belonging to the given board, ordered by column_display_order."""
        ...

    async def update_column_record(
        self, column_entity_to_persist: BoardColumnEntity
    ) -> BoardColumnEntity:
        """Persist changes to an existing column record and return it as stored."""
        ...

    async def delete_column_by_identifier(self, column_identifier: str) -> None:
        """Delete the column with the given identifier. Does not cascade to tasks."""
        ...

    async def delete_columns_by_parent_board_identifier(self, parent_board_identifier: str) -> None:
        """Delete every column belonging to the given board."""
        ...
