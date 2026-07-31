"""Beanie document schema for the project board collection."""

from __future__ import annotations

from datetime import UTC, datetime

from beanie import Document, Indexed
from pydantic import Field


class ProjectBoardDocument(Document):
    """MongoDB document persisting a Kanban board owned by a single user."""

    owning_user_identifier: Indexed(str)  # type: ignore[valid-type]
    board_title: str
    board_description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        """Beanie collection configuration for project board documents."""

        name = "project_boards"
