"""Domain exception hierarchy shared across the authentication, board, column, and task
aggregates."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all business-rule violations raised by the domain and application layers."""


class ResourceNotFoundError(DomainError):
    """Base class for errors indicating that a requested entity does not exist."""


class UnauthorizedAccessError(DomainError):
    """Base class for errors indicating the authenticated user may not act on a resource."""


class ResourceConflictError(DomainError):
    """Base class for errors indicating a request conflicts with existing resource state."""


class AuthenticationError(DomainError):
    """Base class for errors indicating that credentials or a token could not be verified."""


__all__ = [
    "DomainError",
    "ResourceNotFoundError",
    "UnauthorizedAccessError",
    "ResourceConflictError",
    "AuthenticationError",
]
