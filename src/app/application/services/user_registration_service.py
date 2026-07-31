"""Use case for registering a new user account."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.security_password_hashing import hash_plain_text_password
from app.domain.entities.registered_user_entity import RegisteredUserEntity
from app.domain.exceptions.authentication_exceptions import EmailAddressAlreadyRegisteredError
from app.domain.repositories.user_repository_interface import UserRepositoryInterface


class UserRegistrationService:
    """Registers new user accounts, enforcing unique email addresses and hashing passwords."""

    def __init__(self, user_repository: UserRepositoryInterface) -> None:
        """Store the repository used to check for existing accounts and persist new ones."""
        self._user_repository = user_repository

    async def register_new_user_account(
        self, email_address: str, plain_text_password: str, display_name: str
    ) -> RegisteredUserEntity:
        """Create and persist a new user account, rejecting already-registered email addresses."""
        existing_user_with_email = await self._user_repository.find_user_by_email_address(
            email_address
        )
        if existing_user_with_email is not None:
            raise EmailAddressAlreadyRegisteredError(
                f"An account with the email address '{email_address}' already exists."
            )

        new_user_entity = RegisteredUserEntity(
            user_identifier="",
            email_address=email_address,
            hashed_password_value=hash_plain_text_password(plain_text_password),
            display_name=display_name,
            account_created_at=datetime.now(UTC),
            is_account_active=True,
        )

        return await self._user_repository.create_user_record(new_user_entity)
