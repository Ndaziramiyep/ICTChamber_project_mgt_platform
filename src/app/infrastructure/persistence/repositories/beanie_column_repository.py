"""Beanie-backed implementation of the column repository interface."""

from __future__ import annotations

import pymongo
from beanie import PydanticObjectId

from app.domain.entities.board_column_entity import BoardColumnEntity
from app.infrastructure.persistence.documents.column_document import BoardColumnDocument


def _map_column_document_to_entity(column_document: BoardColumnDocument) -> BoardColumnEntity:
    """Convert a persisted BoardColumnDocument into a framework-agnostic domain entity."""
    return BoardColumnEntity(
        column_identifier=str(column_document.id),
        parent_board_identifier=column_document.parent_board_identifier,
        column_title=column_document.column_title,
        column_display_order=column_document.column_display_order,
        created_at=column_document.created_at,
        updated_at=column_document.updated_at,
    )


class BeanieColumnRepository:
    """Persists and retrieves board columns using the Beanie ODM."""

    async def create_column_record(
        self, column_entity_to_persist: BoardColumnEntity
    ) -> BoardColumnEntity:
        """Persist a new column record and return it with its generated identifier populated."""
        new_column_document = BoardColumnDocument(
            parent_board_identifier=column_entity_to_persist.parent_board_identifier,
            column_title=column_entity_to_persist.column_title,
            column_display_order=column_entity_to_persist.column_display_order,
            created_at=column_entity_to_persist.created_at,
            updated_at=column_entity_to_persist.updated_at,
        )
        await new_column_document.insert()
        return _map_column_document_to_entity(new_column_document)

    async def find_column_by_identifier(self, column_identifier: str) -> BoardColumnEntity | None:
        """Return the column with the given identifier, or None if it does not exist or is
        invalid."""
        if not PydanticObjectId.is_valid(column_identifier):
            return None

        found_column_document = await BoardColumnDocument.get(PydanticObjectId(column_identifier))
        return (
            _map_column_document_to_entity(found_column_document) if found_column_document else None
        )

    async def find_columns_by_parent_board_identifier(
        self, parent_board_identifier: str
    ) -> list[BoardColumnEntity]:
        """Return every column belonging to the given board, ordered by column_display_order."""
        found_column_documents = (
            await BoardColumnDocument.find(
                BoardColumnDocument.parent_board_identifier == parent_board_identifier
            )
            .sort((BoardColumnDocument.column_display_order, pymongo.ASCENDING))  # type: ignore[arg-type]
            .to_list()
        )
        return [
            _map_column_document_to_entity(column_document)
            for column_document in found_column_documents
        ]

    async def update_column_record(
        self, column_entity_to_persist: BoardColumnEntity
    ) -> BoardColumnEntity:
        """Persist changes to an existing column record and return it as stored."""
        existing_column_document = await BoardColumnDocument.get(
            PydanticObjectId(column_entity_to_persist.column_identifier)
        )
        assert existing_column_document is not None

        existing_column_document.column_title = column_entity_to_persist.column_title
        existing_column_document.column_display_order = (
            column_entity_to_persist.column_display_order
        )
        existing_column_document.updated_at = column_entity_to_persist.updated_at
        await existing_column_document.save()

        return _map_column_document_to_entity(existing_column_document)

    async def delete_column_by_identifier(self, column_identifier: str) -> None:
        """Delete the column with the given identifier."""
        await BoardColumnDocument.find(
            BoardColumnDocument.id == PydanticObjectId(column_identifier)
        ).delete()

    async def delete_columns_by_parent_board_identifier(self, parent_board_identifier: str) -> None:
        """Delete every column belonging to the given board."""
        await BoardColumnDocument.find(
            BoardColumnDocument.parent_board_identifier == parent_board_identifier
        ).delete()
