"""Factory functions building test payloads and entities for Kanban tasks."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.entities.kanban_task_entity import KanbanTaskEntity


def build_kanban_task_entity(
    task_identifier: str = "60c72b2f9b1e8b3f1c8e4d4a",
    parent_column_identifier: str = "60c72b2f9b1e8b3f1c8e4d3a",
    parent_board_identifier: str = "60c72b2f9b1e8b3f1c8e4d2a",
    task_title: str = "Design the login page",
    task_description: str | None = "Create wireframes and a responsive layout.",
    task_position_value: float = 1000.0,
) -> KanbanTaskEntity:
    """Build a KanbanTaskEntity suitable for use in unit and integration tests."""
    current_utc_moment = datetime.now(UTC)
    return KanbanTaskEntity(
        task_identifier=task_identifier,
        parent_column_identifier=parent_column_identifier,
        parent_board_identifier=parent_board_identifier,
        task_title=task_title,
        task_description=task_description,
        task_position_value=task_position_value,
        created_at=current_utc_moment,
        updated_at=current_utc_moment,
    )


def build_task_creation_request_payload(
    task_title: str = "Design the login page",
    task_description: str | None = "Create wireframes and a responsive layout.",
) -> dict[str, str | None]:
    """Build a JSON-serializable task creation request payload for API integration tests."""
    return {"task_title": task_title, "task_description": task_description}
