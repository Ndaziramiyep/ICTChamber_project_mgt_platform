"""Use cases for creating, retrieving, updating, and deleting Kanban tasks (excluding
reordering)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.application.services.board_access_guard import find_board_and_ensure_ownership
from app.application.services.column_access_guard import find_column_and_ensure_board_ownership
from app.domain.entities.kanban_task_entity import KanbanTaskEntity
from app.domain.exceptions.task_domain_exceptions import TaskNotFoundError
from app.domain.repositories.board_repository_interface import BoardRepositoryInterface
from app.domain.repositories.column_repository_interface import ColumnRepositoryInterface
from app.domain.repositories.task_repository_interface import TaskRepositoryInterface
from app.domain.value_objects.task_position_value import DEFAULT_POSITION_GAP


class TaskManagementService:
    """Creates, retrieves, updates, and deletes Kanban tasks, scoped through their parent board."""

    def __init__(
        self,
        task_repository: TaskRepositoryInterface,
        column_repository: ColumnRepositoryInterface,
        board_repository: BoardRepositoryInterface,
    ) -> None:
        """Store the repositories used to manage tasks and to validate their parent column/board."""
        self._task_repository = task_repository
        self._column_repository = column_repository
        self._board_repository = board_repository

    async def create_task_in_column(
        self,
        parent_column_identifier: str,
        requesting_user_identifier: str,
        task_title: str,
        task_description: str | None,
    ) -> KanbanTaskEntity:
        """Create a new task appended to the bottom of the given column, if the user owns it."""
        parent_column_entity = await find_column_and_ensure_board_ownership(
            self._column_repository,
            self._board_repository,
            parent_column_identifier,
            requesting_user_identifier,
        )

        highest_existing_position = (
            await self._task_repository.find_highest_task_position_value_in_column(
                parent_column_identifier
            )
        )
        new_task_position_value = (
            DEFAULT_POSITION_GAP
            if highest_existing_position is None
            else highest_existing_position + DEFAULT_POSITION_GAP
        )

        current_utc_moment = datetime.now(UTC)
        new_task_entity = KanbanTaskEntity(
            task_identifier="",
            parent_column_identifier=parent_column_identifier,
            parent_board_identifier=parent_column_entity.parent_board_identifier,
            task_title=task_title,
            task_description=task_description,
            task_position_value=new_task_position_value,
            created_at=current_utc_moment,
            updated_at=current_utc_moment,
        )
        return await self._task_repository.create_task_record(new_task_entity)

    async def find_tasks_for_column(
        self, parent_column_identifier: str, requesting_user_identifier: str
    ) -> list[KanbanTaskEntity]:
        """Return every task in the given column, ordered by position, if the user owns its
        board."""
        await find_column_and_ensure_board_ownership(
            self._column_repository,
            self._board_repository,
            parent_column_identifier,
            requesting_user_identifier,
        )
        return await self._task_repository.find_tasks_by_parent_column_identifier(
            parent_column_identifier
        )

    async def find_task_owned_by_authenticated_user(
        self, task_identifier: str, requesting_user_identifier: str
    ) -> KanbanTaskEntity:
        """Return the given task if it exists and its board is owned by the requesting user."""
        return await self._find_task_and_ensure_board_ownership(
            task_identifier, requesting_user_identifier
        )

    async def update_task_owned_by_authenticated_user(
        self,
        task_identifier: str,
        requesting_user_identifier: str,
        task_title: str,
        task_description: str | None,
    ) -> KanbanTaskEntity:
        """Update the given task's title and description if its board is owned by the requester."""
        existing_task_entity = await self._find_task_and_ensure_board_ownership(
            task_identifier, requesting_user_identifier
        )
        existing_task_entity.task_title = task_title
        existing_task_entity.task_description = task_description
        existing_task_entity.updated_at = datetime.now(UTC)
        return await self._task_repository.update_task_record(existing_task_entity)

    async def delete_task_owned_by_authenticated_user(
        self, task_identifier: str, requesting_user_identifier: str
    ) -> None:
        """Delete the given task if its board is owned by the requesting user."""
        await self._find_task_and_ensure_board_ownership(
            task_identifier, requesting_user_identifier
        )
        await self._task_repository.delete_task_by_identifier(task_identifier)

    async def _find_task_and_ensure_board_ownership(
        self, task_identifier: str, requesting_user_identifier: str
    ) -> KanbanTaskEntity:
        """Return the task with the given identifier, enforcing that its board is owned by the
        requester."""
        found_task_entity = await self._task_repository.find_task_by_identifier(task_identifier)
        if found_task_entity is None:
            raise TaskNotFoundError(f"Task with identifier '{task_identifier}' was not found.")

        await find_board_and_ensure_ownership(
            self._board_repository,
            found_task_entity.parent_board_identifier,
            requesting_user_identifier,
        )
        return found_task_entity
