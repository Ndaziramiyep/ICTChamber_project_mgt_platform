"""Use cases for creating, retrieving, updating, and deleting board columns."""

from __future__ import annotations

from datetime import UTC, datetime

from app.application.services.board_access_guard import find_board_and_ensure_ownership
from app.application.services.column_access_guard import find_column_and_ensure_board_ownership
from app.domain.entities.board_column_entity import BoardColumnEntity
from app.domain.exceptions.column_domain_exceptions import ColumnDoesNotBelongToBoardError
from app.domain.repositories.board_repository_interface import BoardRepositoryInterface
from app.domain.repositories.column_repository_interface import ColumnRepositoryInterface
from app.domain.repositories.task_repository_interface import TaskRepositoryInterface


class ColumnManagementService:
    """Creates, retrieves, updates, and deletes board columns, scoped to their parent board."""

    def __init__(
        self,
        column_repository: ColumnRepositoryInterface,
        board_repository: BoardRepositoryInterface,
        task_repository: TaskRepositoryInterface,
    ) -> None:
        """Store the repositories used to manage columns and to validate their parent board."""
        self._column_repository = column_repository
        self._board_repository = board_repository
        self._task_repository = task_repository

    async def create_column_for_board(
        self, parent_board_identifier: str, requesting_user_identifier: str, column_title: str
    ) -> BoardColumnEntity:
        """Create a new column appended to the end of the given board, if the user owns it."""
        await find_board_and_ensure_ownership(
            self._board_repository, parent_board_identifier, requesting_user_identifier
        )

        existing_columns = await self._column_repository.find_columns_by_parent_board_identifier(
            parent_board_identifier
        )
        next_display_order = (
            max((column.column_display_order for column in existing_columns), default=-1) + 1
        )

        current_utc_moment = datetime.now(UTC)
        new_column_entity = BoardColumnEntity(
            column_identifier="",
            parent_board_identifier=parent_board_identifier,
            column_title=column_title,
            column_display_order=next_display_order,
            created_at=current_utc_moment,
            updated_at=current_utc_moment,
        )
        return await self._column_repository.create_column_record(new_column_entity)

    async def find_columns_for_board(
        self, parent_board_identifier: str, requesting_user_identifier: str
    ) -> list[BoardColumnEntity]:
        """Return every column belonging to the given board, if it is owned by the requester."""
        await find_board_and_ensure_ownership(
            self._board_repository, parent_board_identifier, requesting_user_identifier
        )
        return await self._column_repository.find_columns_by_parent_board_identifier(
            parent_board_identifier
        )

    async def find_column_owned_by_authenticated_user(
        self, column_identifier: str, requesting_user_identifier: str
    ) -> BoardColumnEntity:
        """Return the given column if it exists and its parent board is owned by the requester."""
        return await find_column_and_ensure_board_ownership(
            self._column_repository,
            self._board_repository,
            column_identifier,
            requesting_user_identifier,
        )

    async def update_column_owned_by_authenticated_user(
        self, column_identifier: str, requesting_user_identifier: str, column_title: str
    ) -> BoardColumnEntity:
        """Rename the given column if its parent board is owned by the requester."""
        existing_column_entity = await find_column_and_ensure_board_ownership(
            self._column_repository,
            self._board_repository,
            column_identifier,
            requesting_user_identifier,
        )
        existing_column_entity.column_title = column_title
        existing_column_entity.updated_at = datetime.now(UTC)
        return await self._column_repository.update_column_record(existing_column_entity)

    async def delete_column_owned_by_authenticated_user(
        self, column_identifier: str, requesting_user_identifier: str
    ) -> None:
        """Delete the given column, cascading to its tasks, if its parent board is owned by the
        requester."""
        await find_column_and_ensure_board_ownership(
            self._column_repository,
            self._board_repository,
            column_identifier,
            requesting_user_identifier,
        )
        await self._task_repository.delete_tasks_by_parent_column_identifier(column_identifier)
        await self._column_repository.delete_column_by_identifier(column_identifier)

    async def reorder_columns_for_board(
        self,
        parent_board_identifier: str,
        requesting_user_identifier: str,
        ordered_column_identifiers: list[str],
    ) -> list[BoardColumnEntity]:
        """Persist a new left-to-right display order for every column of the given board.

        ``ordered_column_identifiers`` must contain every column currently belonging to the board,
        each exactly once, in their desired new order.
        """
        await find_board_and_ensure_ownership(
            self._board_repository, parent_board_identifier, requesting_user_identifier
        )

        existing_column_entities = (
            await self._column_repository.find_columns_by_parent_board_identifier(
                parent_board_identifier
            )
        )
        existing_columns_by_identifier = {
            column_entity.column_identifier: column_entity
            for column_entity in existing_column_entities
        }
        if len(ordered_column_identifiers) != len(existing_column_entities) or set(
            ordered_column_identifiers
        ) != set(existing_columns_by_identifier.keys()):
            raise ColumnDoesNotBelongToBoardError(
                "The reorder request must include every column belonging to this board exactly "
                "once."
            )

        current_utc_moment = datetime.now(UTC)
        reordered_column_entities: list[BoardColumnEntity] = []
        for new_display_order, column_identifier in enumerate(ordered_column_identifiers):
            column_entity = existing_columns_by_identifier[column_identifier]
            column_entity.column_display_order = new_display_order
            column_entity.updated_at = current_utc_moment
            reordered_column_entities.append(
                await self._column_repository.update_column_record(column_entity)
            )
        return reordered_column_entities
