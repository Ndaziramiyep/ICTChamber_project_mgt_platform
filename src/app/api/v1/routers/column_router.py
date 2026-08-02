"""HTTP routes for creating, retrieving, updating, and deleting board columns."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies.current_user_dependency import get_current_authenticated_user
from app.api.v1.dependencies.service_providers import provide_column_management_service
from app.api.v1.schemas.column_schemas import (
    ColumnCreationRequestSchema,
    ColumnReorderRequestSchema,
    ColumnResponseSchema,
    ColumnUpdateRequestSchema,
)
from app.application.services.column_management_service import ColumnManagementService
from app.domain.entities.board_column_entity import BoardColumnEntity
from app.domain.entities.registered_user_entity import RegisteredUserEntity

column_router = APIRouter(tags=["columns"])


def _map_column_entity_to_response(column_entity: BoardColumnEntity) -> ColumnResponseSchema:
    """Convert a BoardColumnEntity into its public HTTP representation."""
    return ColumnResponseSchema(
        column_identifier=column_entity.column_identifier,
        parent_board_identifier=column_entity.parent_board_identifier,
        column_title=column_entity.column_title,
        column_display_order=column_entity.column_display_order,
        created_at=column_entity.created_at,
        updated_at=column_entity.updated_at,
    )


@column_router.post(
    "/boards/{board_identifier}/columns",
    response_model=ColumnResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_column_for_board(
    board_identifier: str,
    column_creation_request: ColumnCreationRequestSchema,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    column_management_service: ColumnManagementService = Depends(provide_column_management_service),
) -> ColumnResponseSchema:
    """Create a new column appended to the end of the given board."""
    created_column_entity = await column_management_service.create_column_for_board(
        parent_board_identifier=board_identifier,
        requesting_user_identifier=current_authenticated_user.user_identifier,
        column_title=column_creation_request.column_title,
    )
    return _map_column_entity_to_response(created_column_entity)


@column_router.get("/boards/{board_identifier}/columns", response_model=list[ColumnResponseSchema])
async def list_columns_for_board(
    board_identifier: str,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    column_management_service: ColumnManagementService = Depends(provide_column_management_service),
) -> list[ColumnResponseSchema]:
    """Return every column belonging to the given board, ordered by display order."""
    column_entities = await column_management_service.find_columns_for_board(
        parent_board_identifier=board_identifier,
        requesting_user_identifier=current_authenticated_user.user_identifier,
    )
    return [_map_column_entity_to_response(column_entity) for column_entity in column_entities]


@column_router.put(
    "/boards/{board_identifier}/columns/reorder",
    response_model=list[ColumnResponseSchema],
)
async def reorder_columns_for_board(
    board_identifier: str,
    column_reorder_request: ColumnReorderRequestSchema,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    column_management_service: ColumnManagementService = Depends(provide_column_management_service),
) -> list[ColumnResponseSchema]:
    """Persist a new left-to-right display order for every column belonging to the given board."""
    reordered_column_entities = await column_management_service.reorder_columns_for_board(
        parent_board_identifier=board_identifier,
        requesting_user_identifier=current_authenticated_user.user_identifier,
        ordered_column_identifiers=column_reorder_request.ordered_column_identifiers,
    )
    return [
        _map_column_entity_to_response(column_entity) for column_entity in reordered_column_entities
    ]


@column_router.get("/columns/{column_identifier}", response_model=ColumnResponseSchema)
async def get_column_by_identifier(
    column_identifier: str,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    column_management_service: ColumnManagementService = Depends(provide_column_management_service),
) -> ColumnResponseSchema:
    """Return a single column belonging to a board owned by the currently authenticated user."""
    found_column_entity = await column_management_service.find_column_owned_by_authenticated_user(
        column_identifier=column_identifier,
        requesting_user_identifier=current_authenticated_user.user_identifier,
    )
    return _map_column_entity_to_response(found_column_entity)


@column_router.put("/columns/{column_identifier}", response_model=ColumnResponseSchema)
async def update_column_by_identifier(
    column_identifier: str,
    column_update_request: ColumnUpdateRequestSchema,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    column_management_service: ColumnManagementService = Depends(provide_column_management_service),
) -> ColumnResponseSchema:
    """Rename a column belonging to a board owned by the currently authenticated user."""
    updated_column_entity = (
        await column_management_service.update_column_owned_by_authenticated_user(
            column_identifier=column_identifier,
            requesting_user_identifier=current_authenticated_user.user_identifier,
            column_title=column_update_request.column_title,
        )
    )
    return _map_column_entity_to_response(updated_column_entity)


@column_router.delete("/columns/{column_identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column_by_identifier(
    column_identifier: str,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    column_management_service: ColumnManagementService = Depends(provide_column_management_service),
) -> None:
    """Delete a column belonging to a board owned by the currently authenticated user."""
    await column_management_service.delete_column_owned_by_authenticated_user(
        column_identifier=column_identifier,
        requesting_user_identifier=current_authenticated_user.user_identifier,
    )
