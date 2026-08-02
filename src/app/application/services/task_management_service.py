"""Use cases for creating, retrieving, updating, deleting, and repositioning Kanban tasks."""

from __future__ import annotations

from datetime import UTC, datetime

from app.application.services.board_access_guard import find_board_and_ensure_ownership
from app.application.services.column_access_guard import find_column_and_ensure_board_ownership
from app.domain.entities.kanban_task_entity import KanbanTaskEntity
from app.domain.exceptions.task_domain_exceptions import (
    InvalidReorderTargetError,
    TaskNotFoundError,
)
from app.domain.repositories.board_repository_interface import BoardRepositoryInterface
from app.domain.repositories.column_repository_interface import ColumnRepositoryInterface
from app.domain.repositories.task_repository_interface import TaskRepositoryInterface
from app.domain.value_objects.task_position_value import (
    DEFAULT_POSITION_GAP,
    calculate_position_between_neighbors,
    generate_sequential_position_values,
    requires_position_rebalance,
)


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

    async def reposition_task_owned_by_authenticated_user(
        self,
        task_identifier: str,
        requesting_user_identifier: str,
        target_column_identifier: str,
        previous_task_identifier: str | None,
        next_task_identifier: str | None,
    ) -> KanbanTaskEntity:
        """Move a task to a new column and/or position among its new siblings, persisting the
        change.

        The task is placed immediately after ``previous_task_identifier`` and before
        ``next_task_identifier``; either may be ``None`` to mean the top/bottom of the target
        column. Both repository owners (the task's current board and the target column's board)
        must be the requesting user.
        """
        moving_task_entity = await self._find_task_and_ensure_board_ownership(
            task_identifier, requesting_user_identifier
        )
        target_column_entity = await find_column_and_ensure_board_ownership(
            self._column_repository,
            self._board_repository,
            target_column_identifier,
            requesting_user_identifier,
        )

        sibling_task_entities = [
            task_entity
            for task_entity in await self._task_repository.find_tasks_by_parent_column_identifier(
                target_column_identifier
            )
            if task_entity.task_identifier != moving_task_entity.task_identifier
        ]
        insertion_index = self._resolve_insertion_index(
            [task_entity.task_identifier for task_entity in sibling_task_entities],
            previous_task_identifier,
            next_task_identifier,
        )

        position_before_value = (
            sibling_task_entities[insertion_index - 1].task_position_value
            if insertion_index > 0
            else None
        )
        position_after_value = (
            sibling_task_entities[insertion_index].task_position_value
            if insertion_index < len(sibling_task_entities)
            else None
        )

        current_utc_moment = datetime.now(UTC)
        moving_task_entity.parent_column_identifier = target_column_identifier
        moving_task_entity.parent_board_identifier = target_column_entity.parent_board_identifier
        moving_task_entity.updated_at = current_utc_moment

        if requires_position_rebalance(position_before_value, position_after_value):
            ordered_sibling_entities = (
                sibling_task_entities[:insertion_index]
                + [moving_task_entity]
                + sibling_task_entities[insertion_index:]
            )
            sequential_position_values = generate_sequential_position_values(
                len(ordered_sibling_entities)
            )
            for task_entity, sequential_position_value in zip(
                ordered_sibling_entities, sequential_position_values, strict=True
            ):
                task_entity.task_position_value = sequential_position_value
                task_entity.updated_at = current_utc_moment
                await self._task_repository.update_task_record(task_entity)
        else:
            moving_task_entity.task_position_value = calculate_position_between_neighbors(
                position_before_value, position_after_value
            )
            await self._task_repository.update_task_record(moving_task_entity)

        return moving_task_entity

    @staticmethod
    def _resolve_insertion_index(
        sibling_task_identifiers: list[str],
        previous_task_identifier: str | None,
        next_task_identifier: str | None,
    ) -> int:
        """Return the index among ``sibling_task_identifiers`` at which the moving task should be
        inserted, validating that any given neighbor identifiers actually belong to that column
        and are adjacent to one another."""
        if previous_task_identifier is not None:
            if previous_task_identifier not in sibling_task_identifiers:
                raise InvalidReorderTargetError(
                    f"Task with identifier '{previous_task_identifier}' does not belong to the "
                    "target column."
                )
            insertion_index = sibling_task_identifiers.index(previous_task_identifier) + 1
            if next_task_identifier is not None and (
                insertion_index >= len(sibling_task_identifiers)
                or sibling_task_identifiers[insertion_index] != next_task_identifier
            ):
                raise InvalidReorderTargetError(
                    "previous_task_identifier and next_task_identifier are not adjacent siblings "
                    "in the target column."
                )
            return insertion_index

        if next_task_identifier is not None:
            if next_task_identifier not in sibling_task_identifiers:
                raise InvalidReorderTargetError(
                    f"Task with identifier '{next_task_identifier}' does not belong to the target "
                    "column."
                )
            return sibling_task_identifiers.index(next_task_identifier)

        return len(sibling_task_identifiers)

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
