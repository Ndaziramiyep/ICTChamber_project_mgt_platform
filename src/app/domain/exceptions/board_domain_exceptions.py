"""Exceptions raised by the board management use cases."""

from __future__ import annotations

from app.domain.exceptions import ResourceNotFoundError, UnauthorizedAccessError


class BoardNotFoundError(ResourceNotFoundError):
    """Raised when a referenced board does not exist."""


class UnauthorizedBoardAccessError(UnauthorizedAccessError):
    """Raised when the authenticated user does not own the board they are trying to access."""
