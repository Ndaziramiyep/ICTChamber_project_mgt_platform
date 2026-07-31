"""Abstract persistence contract for registered user accounts."""

from __future__ import annotations

from typing import Protocol

from app.domain.entities.registered_user_entity import RegisteredUserEntity


class UserRepositoryInterface(Protocol):
    """Persistence operations required by the authentication use cases."""

    async def create_user_record(
        self, user_entity_to_persist: RegisteredUserEntity
    ) -> RegisteredUserEntity:
        """Persist a new user record and return it as stored."""
        ...

    async def find_user_by_email_address(self, email_address: str) -> RegisteredUserEntity | None:
        """Return the user with the given email address, or None if no such user exists."""
        ...

    async def find_user_by_identifier(self, user_identifier: str) -> RegisteredUserEntity | None:
        """Return the user with the given identifier, or None if no such user exists."""
        ...
