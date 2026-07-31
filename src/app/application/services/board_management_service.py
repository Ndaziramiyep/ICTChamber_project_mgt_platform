"""Use cases for creating, retrieving, updating, and deleting project boards."""

from __future__ import annotations

from datetime import UTC, datetime

from app.application.services.board_access_guard import find_board_and_ensure_ownership
from app.domain.entities.project_board_entity import ProjectBoardEntity
from app.domain.repositories.board_repository_interface import BoardRepositoryInterface


class BoardManagementService:
    """Creates, retrieves, updates, and deletes project boards, enforcing owner-based access."""

    def __init__(self, board_repository: BoardRepositoryInterface) -> None:
        """Store the repository used to persist and retrieve board records."""
        self._board_repository = board_repository

    async def create_board_for_authenticated_user(
        self, owning_user_identifier: str, board_title: str, board_description: str | None
    ) -> ProjectBoardEntity:
        """Create and persist a new board owned by the given authenticated user."""
        current_utc_moment = datetime.now(UTC)
        new_board_entity = ProjectBoardEntity(
            board_identifier="",
            owning_user_identifier=owning_user_identifier,
            board_title=board_title,
            board_description=board_description,
            created_at=current_utc_moment,
            updated_at=current_utc_moment,
        )
        return await self._board_repository.create_board_record(new_board_entity)

    async def find_boards_owned_by_authenticated_user(
        self, owning_user_identifier: str
    ) -> list[ProjectBoardEntity]:
        """Return every board owned by the given authenticated user."""
        return await self._board_repository.find_boards_owned_by_user_identifier(
            owning_user_identifier
        )

    async def find_board_owned_by_authenticated_user(
        self, board_identifier: str, requesting_user_identifier: str
    ) -> ProjectBoardEntity:
        """Return the given board if it exists and is owned by the requesting user."""
        return await find_board_and_ensure_ownership(
            self._board_repository, board_identifier, requesting_user_identifier
        )

    async def update_board_owned_by_authenticated_user(
        self,
        board_identifier: str,
        requesting_user_identifier: str,
        board_title: str,
        board_description: str | None,
    ) -> ProjectBoardEntity:
        """Update the given board's title and description if owned by the requesting user."""
        existing_board_entity = await find_board_and_ensure_ownership(
            self._board_repository, board_identifier, requesting_user_identifier
        )
        existing_board_entity.board_title = board_title
        existing_board_entity.board_description = board_description
        existing_board_entity.updated_at = datetime.now(UTC)
        return await self._board_repository.update_board_record(existing_board_entity)

    async def delete_board_owned_by_authenticated_user(
        self, board_identifier: str, requesting_user_identifier: str
    ) -> None:
        """Delete the given board if it is owned by the requesting user."""
        await find_board_and_ensure_ownership(
            self._board_repository, board_identifier, requesting_user_identifier
        )
        await self._board_repository.delete_board_by_identifier(board_identifier)
