"""Beanie document schema for the board column collection."""

from __future__ import annotations

from datetime import UTC, datetime

import pymongo
from beanie import Document
from pydantic import Field


class BoardColumnDocument(Document):
    """MongoDB document persisting a single column within a project board."""

    parent_board_identifier: str
    column_title: str
    column_display_order: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        """Beanie collection configuration for board column documents."""

        name = "board_columns"
        indexes = [
            [
                ("parent_board_identifier", pymongo.ASCENDING),
                ("column_display_order", pymongo.ASCENDING),
            ],
        ]
