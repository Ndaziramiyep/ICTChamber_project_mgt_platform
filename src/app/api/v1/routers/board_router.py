"""HTTP routes for creating, retrieving, updating, and deleting project boards."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies.current_user_dependency import get_current_authenticated_user
from app.api.v1.dependencies.service_providers import provide_board_management_service
from app.api.v1.schemas.board_schemas import (
    BoardCreationRequestSchema,
    BoardResponseSchema,
    BoardUpdateRequestSchema,
)
from app.application.services.board_management_service import BoardManagementService
from app.domain.entities.project_board_entity import ProjectBoardEntity
from app.domain.entities.registered_user_entity import RegisteredUserEntity

board_router = APIRouter(prefix="/boards", tags=["boards"])


def _map_board_entity_to_response(board_entity: ProjectBoardEntity) -> BoardResponseSchema:
    """Convert a ProjectBoardEntity into its public HTTP representation."""
    return BoardResponseSchema(
        board_identifier=board_entity.board_identifier,
        owning_user_identifier=board_entity.owning_user_identifier,
        board_title=board_entity.board_title,
        board_description=board_entity.board_description,
        created_at=board_entity.created_at,
        updated_at=board_entity.updated_at,
    )


@board_router.post("", response_model=BoardResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_new_board(
    board_creation_request: BoardCreationRequestSchema,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    board_management_service: BoardManagementService = Depends(provide_board_management_service),
) -> BoardResponseSchema:
    """Create a new board owned by the currently authenticated user."""
    created_board_entity = await board_management_service.create_board_for_authenticated_user(
        owning_user_identifier=current_authenticated_user.user_identifier,
        board_title=board_creation_request.board_title,
        board_description=board_creation_request.board_description,
    )
    return _map_board_entity_to_response(created_board_entity)


@board_router.get("", response_model=list[BoardResponseSchema])
async def list_boards_owned_by_authenticated_user(
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    board_management_service: BoardManagementService = Depends(provide_board_management_service),
) -> list[BoardResponseSchema]:
    """Return every board owned by the currently authenticated user."""
    owned_board_entities = await board_management_service.find_boards_owned_by_authenticated_user(
        owning_user_identifier=current_authenticated_user.user_identifier
    )
    return [_map_board_entity_to_response(board_entity) for board_entity in owned_board_entities]


@board_router.get("/{board_identifier}", response_model=BoardResponseSchema)
async def get_board_by_identifier(
    board_identifier: str,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    board_management_service: BoardManagementService = Depends(provide_board_management_service),
) -> BoardResponseSchema:
    """Return a single board owned by the currently authenticated user."""
    found_board_entity = await board_management_service.find_board_owned_by_authenticated_user(
        board_identifier=board_identifier,
        requesting_user_identifier=current_authenticated_user.user_identifier,
    )
    return _map_board_entity_to_response(found_board_entity)


@board_router.put("/{board_identifier}", response_model=BoardResponseSchema)
async def update_board_by_identifier(
    board_identifier: str,
    board_update_request: BoardUpdateRequestSchema,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    board_management_service: BoardManagementService = Depends(provide_board_management_service),
) -> BoardResponseSchema:
    """Update the title and description of a board owned by the currently authenticated user."""
    updated_board_entity = await board_management_service.update_board_owned_by_authenticated_user(
        board_identifier=board_identifier,
        requesting_user_identifier=current_authenticated_user.user_identifier,
        board_title=board_update_request.board_title,
        board_description=board_update_request.board_description,
    )
    return _map_board_entity_to_response(updated_board_entity)


@board_router.delete("/{board_identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board_by_identifier(
    board_identifier: str,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    board_management_service: BoardManagementService = Depends(provide_board_management_service),
) -> None:
    """Delete a board owned by the currently authenticated user."""
    await board_management_service.delete_board_owned_by_authenticated_user(
        board_identifier=board_identifier,
        requesting_user_identifier=current_authenticated_user.user_identifier,
    )
