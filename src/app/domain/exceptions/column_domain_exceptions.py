"""Exceptions raised by the column management use cases."""

from __future__ import annotations

from app.domain.exceptions import ResourceNotFoundError


class ColumnNotFoundError(ResourceNotFoundError):
    """Raised when a referenced column does not exist."""


class ColumnDoesNotBelongToBoardError(ResourceNotFoundError):
    """Raised when a column is referenced under a board it does not actually belong to."""
