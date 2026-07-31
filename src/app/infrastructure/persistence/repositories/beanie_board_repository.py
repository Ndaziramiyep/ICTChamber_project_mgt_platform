"""Beanie-backed implementation of the board repository interface."""

from __future__ import annotations

from beanie import PydanticObjectId

from app.domain.entities.project_board_entity import ProjectBoardEntity
from app.infrastructure.persistence.documents.board_document import ProjectBoardDocument


def _map_board_document_to_entity(board_document: ProjectBoardDocument) -> ProjectBoardEntity:
    """Convert a persisted ProjectBoardDocument into a framework-agnostic domain entity."""
    return ProjectBoardEntity(
        board_identifier=str(board_document.id),
        owning_user_identifier=board_document.owning_user_identifier,
        board_title=board_document.board_title,
        board_description=board_document.board_description,
        created_at=board_document.created_at,
        updated_at=board_document.updated_at,
    )


class BeanieBoardRepository:
    """Persists and retrieves project boards using the Beanie ODM."""

    async def create_board_record(
        self, board_entity_to_persist: ProjectBoardEntity
    ) -> ProjectBoardEntity:
        """Persist a new board record and return it with its generated identifier populated."""
        new_board_document = ProjectBoardDocument(
            owning_user_identifier=board_entity_to_persist.owning_user_identifier,
            board_title=board_entity_to_persist.board_title,
            board_description=board_entity_to_persist.board_description,
            created_at=board_entity_to_persist.created_at,
            updated_at=board_entity_to_persist.updated_at,
        )
        await new_board_document.insert()
        return _map_board_document_to_entity(new_board_document)

    async def find_board_by_identifier(self, board_identifier: str) -> ProjectBoardEntity | None:
        """Return the board with the given identifier, or None if it does not exist or is
        invalid."""
        if not PydanticObjectId.is_valid(board_identifier):
            return None

        found_board_document = await ProjectBoardDocument.get(PydanticObjectId(board_identifier))
        return _map_board_document_to_entity(found_board_document) if found_board_document else None

    async def find_boards_owned_by_user_identifier(
        self, owning_user_identifier: str
    ) -> list[ProjectBoardEntity]:
        """Return every board owned by the given user."""
        found_board_documents = await ProjectBoardDocument.find(
            ProjectBoardDocument.owning_user_identifier == owning_user_identifier
        ).to_list()
        return [
            _map_board_document_to_entity(board_document)
            for board_document in found_board_documents
        ]

    async def update_board_record(
        self, board_entity_to_persist: ProjectBoardEntity
    ) -> ProjectBoardEntity:
        """Persist changes to an existing board record and return it as stored."""
        existing_board_document = await ProjectBoardDocument.get(
            PydanticObjectId(board_entity_to_persist.board_identifier)
        )
        assert existing_board_document is not None

        existing_board_document.board_title = board_entity_to_persist.board_title
        existing_board_document.board_description = board_entity_to_persist.board_description
        existing_board_document.updated_at = board_entity_to_persist.updated_at
        await existing_board_document.save()

        return _map_board_document_to_entity(existing_board_document)

    async def delete_board_by_identifier(self, board_identifier: str) -> None:
        """Delete the board with the given identifier."""
        await ProjectBoardDocument.find(
            ProjectBoardDocument.id == PydanticObjectId(board_identifier)
        ).delete()
