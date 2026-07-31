"""Beanie document schema for the Kanban task collection."""

from __future__ import annotations

from datetime import UTC, datetime

import pymongo
from beanie import Document
from pydantic import Field


class KanbanTaskDocument(Document):
    """MongoDB document persisting a single task card within a board column."""

    parent_column_identifier: str
    parent_board_identifier: str
    task_title: str
    task_description: str | None = None
    task_position_value: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        """Beanie collection configuration for Kanban task documents."""

        name = "kanban_tasks"
        indexes = [
            [
                ("parent_column_identifier", pymongo.ASCENDING),
                ("task_position_value", pymongo.ASCENDING),
            ],
            [("parent_board_identifier", pymongo.ASCENDING)],
        ]
