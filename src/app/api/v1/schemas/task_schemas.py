"""Request and response schemas for the task management endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TaskCreationRequestSchema(BaseModel):
    """Payload required to create a new task within a column."""

    task_title: str = Field(min_length=1, max_length=200)
    task_description: str | None = Field(default=None, max_length=4000)


class TaskUpdateRequestSchema(BaseModel):
    """Payload required to update an existing task's title and description."""

    task_title: str = Field(min_length=1, max_length=200)
    task_description: str | None = Field(default=None, max_length=4000)


class TaskRepositionRequestSchema(BaseModel):
    """Payload specifying a task's new column and position among its new siblings.

    The task is placed immediately after ``previous_task_identifier`` and before
    ``next_task_identifier``; either may be omitted to mean the top/bottom of the target column.
    """

    target_column_identifier: str
    previous_task_identifier: str | None = None
    next_task_identifier: str | None = None


class TaskResponseSchema(BaseModel):
    """Public representation of a Kanban task."""

    task_identifier: str
    parent_column_identifier: str
    parent_board_identifier: str
    task_title: str
    task_description: str | None
    task_position_value: float
    created_at: datetime
    updated_at: datetime
