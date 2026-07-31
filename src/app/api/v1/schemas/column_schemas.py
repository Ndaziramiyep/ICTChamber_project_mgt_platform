"""Request and response schemas for the column management endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ColumnCreationRequestSchema(BaseModel):
    """Payload required to create a new column within a board."""

    column_title: str = Field(min_length=1, max_length=200)


class ColumnUpdateRequestSchema(BaseModel):
    """Payload required to rename an existing column."""

    column_title: str = Field(min_length=1, max_length=200)


class ColumnResponseSchema(BaseModel):
    """Public representation of a board column."""

    column_identifier: str
    parent_board_identifier: str
    column_title: str
    column_display_order: int
    created_at: datetime
    updated_at: datetime
