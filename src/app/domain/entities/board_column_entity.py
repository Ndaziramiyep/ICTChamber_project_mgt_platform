"""Domain entity representing a single column (list) within a Kanban board."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class BoardColumnEntity:
    """A column that groups an ordered set of tasks within a single parent board."""

    column_identifier: str
    parent_board_identifier: str
    column_title: str
    column_display_order: int
    created_at: datetime
    updated_at: datetime
