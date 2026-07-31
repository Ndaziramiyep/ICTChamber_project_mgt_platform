"""Domain entity representing a Kanban board owned by a registered user."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProjectBoardEntity:
    """A Kanban board that groups columns and tasks under a single project, owned by one user."""

    board_identifier: str
    owning_user_identifier: str
    board_title: str
    board_description: str | None
    created_at: datetime
    updated_at: datetime
