"""Shared guard for confirming a requesting user owns a given board.

Extracted so that every service needing to authorize access to a board (boards, columns, and
tasks all scope their operations through a parent board) enforces the same ownership rule via a
single code path, rather than each service re-implementing the same not-found/forbidden check.
"""

from __future__ import annotations

from app.domain.entities.project_board_entity import ProjectBoardEntity
from app.domain.exceptions.board_domain_exceptions import (
    BoardNotFoundError,
    UnauthorizedBoardAccessError,
)
from app.domain.repositories.board_repository_interface import BoardRepositoryInterface


async def find_board_and_ensure_ownership(
    board_repository: BoardRepositoryInterface,
    board_identifier: str,
    requesting_user_identifier: str,
) -> ProjectBoardEntity:
    """Return the board with the given identifier, enforcing that the requester owns it."""
    found_board_entity = await board_repository.find_board_by_identifier(board_identifier)
    if found_board_entity is None:
        raise BoardNotFoundError(f"Board with identifier '{board_identifier}' was not found.")
    if found_board_entity.owning_user_identifier != requesting_user_identifier:
        raise UnauthorizedBoardAccessError(
            "The authenticated user does not have access to this board."
        )
    return found_board_entity
