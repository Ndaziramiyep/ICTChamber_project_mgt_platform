"""Abstract persistence contract for project boards."""

from __future__ import annotations

from typing import Protocol

from app.domain.entities.project_board_entity import ProjectBoardEntity


class BoardRepositoryInterface(Protocol):
    """Persistence operations required by the board management use cases."""

    async def create_board_record(
        self, board_entity_to_persist: ProjectBoardEntity
    ) -> ProjectBoardEntity:
        """Persist a new board record and return it as stored."""
        ...

    async def find_board_by_identifier(self, board_identifier: str) -> ProjectBoardEntity | None:
        """Return the board with the given identifier, or None if no such board exists."""
        ...

    async def find_boards_owned_by_user_identifier(
        self, owning_user_identifier: str
    ) -> list[ProjectBoardEntity]:
        """Return every board owned by the given user, in no particular guaranteed order."""
        ...

    async def update_board_record(
        self, board_entity_to_persist: ProjectBoardEntity
    ) -> ProjectBoardEntity:
        """Persist changes to an existing board record and return it as stored."""
        ...

    async def delete_board_by_identifier(self, board_identifier: str) -> None:
        """Delete the board with the given identifier. Does not cascade to columns or tasks."""
        ...
