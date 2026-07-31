"""Request and response schemas for the board management endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BoardCreationRequestSchema(BaseModel):
    """Payload required to create a new board."""

    board_title: str = Field(min_length=1, max_length=200)
    board_description: str | None = Field(default=None, max_length=2000)


class BoardUpdateRequestSchema(BaseModel):
    """Payload required to update an existing board's title and description."""

    board_title: str = Field(min_length=1, max_length=200)
    board_description: str | None = Field(default=None, max_length=2000)


class BoardResponseSchema(BaseModel):
    """Public representation of a project board."""

    board_identifier: str
    owning_user_identifier: str
    board_title: str
    board_description: str | None
    created_at: datetime
    updated_at: datetime
