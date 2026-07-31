"""Beanie-backed implementation of the task repository interface."""

from __future__ import annotations

import pymongo
from beanie import PydanticObjectId

from app.domain.entities.kanban_task_entity import KanbanTaskEntity
from app.infrastructure.persistence.documents.task_document import KanbanTaskDocument


def _map_task_document_to_entity(task_document: KanbanTaskDocument) -> KanbanTaskEntity:
    """Convert a persisted KanbanTaskDocument into a framework-agnostic domain entity."""
    return KanbanTaskEntity(
        task_identifier=str(task_document.id),
        parent_column_identifier=task_document.parent_column_identifier,
        parent_board_identifier=task_document.parent_board_identifier,
        task_title=task_document.task_title,
        task_description=task_document.task_description,
        task_position_value=task_document.task_position_value,
        created_at=task_document.created_at,
        updated_at=task_document.updated_at,
    )


class BeanieTaskRepository:
    """Persists and retrieves Kanban tasks using the Beanie ODM."""

    async def create_task_record(
        self, task_entity_to_persist: KanbanTaskEntity
    ) -> KanbanTaskEntity:
        """Persist a new task record and return it with its generated identifier populated."""
        new_task_document = KanbanTaskDocument(
            parent_column_identifier=task_entity_to_persist.parent_column_identifier,
            parent_board_identifier=task_entity_to_persist.parent_board_identifier,
            task_title=task_entity_to_persist.task_title,
            task_description=task_entity_to_persist.task_description,
            task_position_value=task_entity_to_persist.task_position_value,
            created_at=task_entity_to_persist.created_at,
            updated_at=task_entity_to_persist.updated_at,
        )
        await new_task_document.insert()
        return _map_task_document_to_entity(new_task_document)

    async def find_task_by_identifier(self, task_identifier: str) -> KanbanTaskEntity | None:
        """Return the task with the given identifier, or None if it does not exist or is invalid."""
        if not PydanticObjectId.is_valid(task_identifier):
            return None

        found_task_document = await KanbanTaskDocument.get(PydanticObjectId(task_identifier))
        return _map_task_document_to_entity(found_task_document) if found_task_document else None

    async def find_tasks_by_parent_column_identifier(
        self, parent_column_identifier: str
    ) -> list[KanbanTaskEntity]:
        """Return every task in the given column, ordered ascending by task_position_value."""
        found_task_documents = (
            await KanbanTaskDocument.find(
                KanbanTaskDocument.parent_column_identifier == parent_column_identifier
            )
            .sort((KanbanTaskDocument.task_position_value, pymongo.ASCENDING))  # type: ignore[arg-type]
            .to_list()
        )
        return [
            _map_task_document_to_entity(task_document) for task_document in found_task_documents
        ]

    async def find_highest_task_position_value_in_column(
        self, parent_column_identifier: str
    ) -> float | None:
        """Return the highest task_position_value in the given column, or None if it is empty."""
        highest_positioned_task_document = (
            await KanbanTaskDocument.find(
                KanbanTaskDocument.parent_column_identifier == parent_column_identifier
            )
            .sort((KanbanTaskDocument.task_position_value, pymongo.DESCENDING))  # type: ignore[arg-type]
            .first_or_none()
        )

        return (
            highest_positioned_task_document.task_position_value
            if highest_positioned_task_document
            else None
        )

    async def update_task_record(
        self, task_entity_to_persist: KanbanTaskEntity
    ) -> KanbanTaskEntity:
        """Persist changes to an existing task record and return it as stored."""
        existing_task_document = await KanbanTaskDocument.get(
            PydanticObjectId(task_entity_to_persist.task_identifier)
        )
        assert existing_task_document is not None

        existing_task_document.parent_column_identifier = (
            task_entity_to_persist.parent_column_identifier
        )
        existing_task_document.task_title = task_entity_to_persist.task_title
        existing_task_document.task_description = task_entity_to_persist.task_description
        existing_task_document.task_position_value = task_entity_to_persist.task_position_value
        existing_task_document.updated_at = task_entity_to_persist.updated_at
        await existing_task_document.save()

        return _map_task_document_to_entity(existing_task_document)

    async def delete_task_by_identifier(self, task_identifier: str) -> None:
        """Delete the task with the given identifier."""
        await KanbanTaskDocument.find(
            KanbanTaskDocument.id == PydanticObjectId(task_identifier)
        ).delete()

    async def delete_tasks_by_parent_column_identifier(self, parent_column_identifier: str) -> None:
        """Delete every task belonging to the given column."""
        await KanbanTaskDocument.find(
            KanbanTaskDocument.parent_column_identifier == parent_column_identifier
        ).delete()

    async def delete_tasks_by_parent_board_identifier(self, parent_board_identifier: str) -> None:
        """Delete every task belonging to the given board, across all of its columns."""
        await KanbanTaskDocument.find(
            KanbanTaskDocument.parent_board_identifier == parent_board_identifier
        ).delete()
