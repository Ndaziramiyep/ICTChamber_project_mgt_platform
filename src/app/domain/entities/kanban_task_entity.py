"""Domain entity representing a single task card placed within a board column."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class KanbanTaskEntity:
    """A task card belonging to one column, ordered among its siblings by task_position_value."""

    task_identifier: str
    parent_column_identifier: str
    parent_board_identifier: str
    task_title: str
    task_description: str | None
    task_position_value: float
    created_at: datetime
    updated_at: datetime
