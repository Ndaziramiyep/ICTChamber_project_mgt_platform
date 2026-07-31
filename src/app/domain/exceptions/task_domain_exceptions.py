"""Exceptions raised by the task management and reordering use cases."""

from __future__ import annotations

from app.domain.exceptions import ResourceNotFoundError


class TaskNotFoundError(ResourceNotFoundError):
    """Raised when a referenced task does not exist."""


class TaskDoesNotBelongToColumnError(ResourceNotFoundError):
    """Raised when a task is referenced under a column it does not actually belong to."""


class InvalidReorderTargetError(ResourceNotFoundError):
    """Raised when a reorder request's neighbor task ids do not belong to the target column."""
