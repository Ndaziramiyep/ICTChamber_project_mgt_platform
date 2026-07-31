"""Factory functions building test payloads and entities for project boards."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.entities.project_board_entity import ProjectBoardEntity


def build_project_board_entity(
    board_identifier: str = "60c72b2f9b1e8b3f1c8e4d2a",
    owning_user_identifier: str = "60c72b2f9b1e8b3f1c8e4d1a",
    board_title: str = "Website Relaunch",
    board_description: str | None = "Tasks for the Q3 website relaunch project.",
) -> ProjectBoardEntity:
    """Build a ProjectBoardEntity suitable for use in unit and integration tests."""
    current_utc_moment = datetime.now(UTC)
    return ProjectBoardEntity(
        board_identifier=board_identifier,
        owning_user_identifier=owning_user_identifier,
        board_title=board_title,
        board_description=board_description,
        created_at=current_utc_moment,
        updated_at=current_utc_moment,
    )


def build_board_creation_request_payload(
    board_title: str = "Website Relaunch",
    board_description: str | None = "Tasks for the Q3 website relaunch project.",
) -> dict[str, str | None]:
    """Build a JSON-serializable board creation request payload for API integration tests."""
    return {"board_title": board_title, "board_description": board_description}
