"""HTTP routes for creating, retrieving, updating, and deleting Kanban tasks."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies.current_user_dependency import get_current_authenticated_user
from app.api.v1.dependencies.service_providers import provide_task_management_service
from app.api.v1.schemas.task_schemas import (
    TaskCreationRequestSchema,
    TaskRepositionRequestSchema,
    TaskResponseSchema,
    TaskUpdateRequestSchema,
)
from app.application.services.task_management_service import TaskManagementService
from app.domain.entities.kanban_task_entity import KanbanTaskEntity
from app.domain.entities.registered_user_entity import RegisteredUserEntity

task_router = APIRouter(tags=["tasks"])


def _map_task_entity_to_response(task_entity: KanbanTaskEntity) -> TaskResponseSchema:
    """Convert a KanbanTaskEntity into its public HTTP representation."""
    return TaskResponseSchema(
        task_identifier=task_entity.task_identifier,
        parent_column_identifier=task_entity.parent_column_identifier,
        parent_board_identifier=task_entity.parent_board_identifier,
        task_title=task_entity.task_title,
        task_description=task_entity.task_description,
        task_position_value=task_entity.task_position_value,
        created_at=task_entity.created_at,
        updated_at=task_entity.updated_at,
    )


@task_router.post(
    "/columns/{column_identifier}/tasks",
    response_model=TaskResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_task_in_column(
    column_identifier: str,
    task_creation_request: TaskCreationRequestSchema,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    task_management_service: TaskManagementService = Depends(provide_task_management_service),
) -> TaskResponseSchema:
    """Create a new task appended to the bottom of the given column."""
    created_task_entity = await task_management_service.create_task_in_column(
        parent_column_identifier=column_identifier,
        requesting_user_identifier=current_authenticated_user.user_identifier,
        task_title=task_creation_request.task_title,
        task_description=task_creation_request.task_description,
    )
    return _map_task_entity_to_response(created_task_entity)


@task_router.get("/columns/{column_identifier}/tasks", response_model=list[TaskResponseSchema])
async def list_tasks_for_column(
    column_identifier: str,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    task_management_service: TaskManagementService = Depends(provide_task_management_service),
) -> list[TaskResponseSchema]:
    """Return every task in the given column, ordered by position."""
    task_entities = await task_management_service.find_tasks_for_column(
        parent_column_identifier=column_identifier,
        requesting_user_identifier=current_authenticated_user.user_identifier,
    )
    return [_map_task_entity_to_response(task_entity) for task_entity in task_entities]


@task_router.get("/tasks/{task_identifier}", response_model=TaskResponseSchema)
async def get_task_by_identifier(
    task_identifier: str,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    task_management_service: TaskManagementService = Depends(provide_task_management_service),
) -> TaskResponseSchema:
    """Return a single task belonging to a board owned by the currently authenticated user."""
    found_task_entity = await task_management_service.find_task_owned_by_authenticated_user(
        task_identifier=task_identifier,
        requesting_user_identifier=current_authenticated_user.user_identifier,
    )
    return _map_task_entity_to_response(found_task_entity)


@task_router.put("/tasks/{task_identifier}", response_model=TaskResponseSchema)
async def update_task_by_identifier(
    task_identifier: str,
    task_update_request: TaskUpdateRequestSchema,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    task_management_service: TaskManagementService = Depends(provide_task_management_service),
) -> TaskResponseSchema:
    """Update the title and description of a task belonging to a board owned by the requester."""
    updated_task_entity = await task_management_service.update_task_owned_by_authenticated_user(
        task_identifier=task_identifier,
        requesting_user_identifier=current_authenticated_user.user_identifier,
        task_title=task_update_request.task_title,
        task_description=task_update_request.task_description,
    )
    return _map_task_entity_to_response(updated_task_entity)


@task_router.patch("/tasks/{task_identifier}/position", response_model=TaskResponseSchema)
async def reposition_task_by_identifier(
    task_identifier: str,
    task_reposition_request: TaskRepositionRequestSchema,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    task_management_service: TaskManagementService = Depends(provide_task_management_service),
) -> TaskResponseSchema:
    """Move a task to a new column and/or position among its new siblings."""
    repositioned_task_entity = (
        await task_management_service.reposition_task_owned_by_authenticated_user(
            task_identifier=task_identifier,
            requesting_user_identifier=current_authenticated_user.user_identifier,
            target_column_identifier=task_reposition_request.target_column_identifier,
            previous_task_identifier=task_reposition_request.previous_task_identifier,
            next_task_identifier=task_reposition_request.next_task_identifier,
        )
    )
    return _map_task_entity_to_response(repositioned_task_entity)


@task_router.delete("/tasks/{task_identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_by_identifier(
    task_identifier: str,
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
    task_management_service: TaskManagementService = Depends(provide_task_management_service),
) -> None:
    """Delete a task belonging to a board owned by the currently authenticated user."""
    await task_management_service.delete_task_owned_by_authenticated_user(
        task_identifier=task_identifier,
        requesting_user_identifier=current_authenticated_user.user_identifier,
    )
