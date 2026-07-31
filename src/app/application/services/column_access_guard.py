"""Shared guard for confirming a requesting user owns the board a column belongs to.

Extracted so that every service needing to authorize access to a column (columns and tasks both
scope their operations through a parent column's board) enforces the same rule via a single code
path, rather than each service re-implementing the same not-found/forbidden check.
"""

from __future__ import annotations

from app.application.services.board_access_guard import find_board_and_ensure_ownership
from app.domain.entities.board_column_entity import BoardColumnEntity
from app.domain.exceptions.column_domain_exceptions import ColumnNotFoundError
from app.domain.repositories.board_repository_interface import BoardRepositoryInterface
from app.domain.repositories.column_repository_interface import ColumnRepositoryInterface


async def find_column_and_ensure_board_ownership(
    column_repository: ColumnRepositoryInterface,
    board_repository: BoardRepositoryInterface,
    column_identifier: str,
    requesting_user_identifier: str,
) -> BoardColumnEntity:
    """Return the column with the given identifier, enforcing that its board is owned by the
    requester."""
    found_column_entity = await column_repository.find_column_by_identifier(column_identifier)
    if found_column_entity is None:
        raise ColumnNotFoundError(f"Column with identifier '{column_identifier}' was not found.")

    await find_board_and_ensure_ownership(
        board_repository, found_column_entity.parent_board_identifier, requesting_user_identifier
    )
    return found_column_entity
