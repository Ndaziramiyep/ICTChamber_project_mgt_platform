"""Exceptions raised by the registration and authentication use cases."""

from __future__ import annotations

from app.domain.exceptions import AuthenticationError, ResourceConflictError


class InvalidCredentialsError(AuthenticationError):
    """Raised when a login attempt supplies an unknown email address or a wrong password."""


class ExpiredTokenError(AuthenticationError):
    """Raised when a JWT has passed its expiry timestamp."""


class InvalidTokenTypeError(AuthenticationError):
    """Raised when a token is presented for a purpose other than the one it was issued for."""


class MalformedTokenError(AuthenticationError):
    """Raised when a token cannot be decoded or fails signature verification."""


class EmailAddressAlreadyRegisteredError(ResourceConflictError):
    """Raised when registration is attempted with an email address already on file."""
