"""Factory functions building test payloads and entities for board columns."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.entities.board_column_entity import BoardColumnEntity


def build_board_column_entity(
    column_identifier: str = "60c72b2f9b1e8b3f1c8e4d3a",
    parent_board_identifier: str = "60c72b2f9b1e8b3f1c8e4d2a",
    column_title: str = "To Do",
    column_display_order: int = 0,
) -> BoardColumnEntity:
    """Build a BoardColumnEntity suitable for use in unit and integration tests."""
    current_utc_moment = datetime.now(UTC)
    return BoardColumnEntity(
        column_identifier=column_identifier,
        parent_board_identifier=parent_board_identifier,
        column_title=column_title,
        column_display_order=column_display_order,
        created_at=current_utc_moment,
        updated_at=current_utc_moment,
    )


def build_column_creation_request_payload(column_title: str = "To Do") -> dict[str, str]:
    """Build a JSON-serializable column creation request payload for API integration tests."""
    return {"column_title": column_title}
