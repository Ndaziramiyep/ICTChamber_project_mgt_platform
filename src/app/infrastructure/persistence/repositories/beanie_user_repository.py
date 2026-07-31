"""Beanie-backed implementation of the user repository interface."""

from __future__ import annotations

from beanie import PydanticObjectId

from app.domain.entities.registered_user_entity import RegisteredUserEntity
from app.infrastructure.persistence.documents.user_document import RegisteredUserDocument


def _map_user_document_to_entity(user_document: RegisteredUserDocument) -> RegisteredUserEntity:
    """Convert a persisted RegisteredUserDocument into a framework-agnostic domain entity."""
    return RegisteredUserEntity(
        user_identifier=str(user_document.id),
        email_address=user_document.email_address,
        hashed_password_value=user_document.hashed_password_value,
        display_name=user_document.display_name,
        account_created_at=user_document.account_created_at,
        is_account_active=user_document.is_account_active,
    )


class BeanieUserRepository:
    """Persists and retrieves registered user accounts using the Beanie ODM."""

    async def create_user_record(
        self, user_entity_to_persist: RegisteredUserEntity
    ) -> RegisteredUserEntity:
        """Persist a new user record and return it with its generated identifier populated."""
        new_user_document = RegisteredUserDocument(
            email_address=user_entity_to_persist.email_address,
            hashed_password_value=user_entity_to_persist.hashed_password_value,
            display_name=user_entity_to_persist.display_name,
            account_created_at=user_entity_to_persist.account_created_at,
            is_account_active=user_entity_to_persist.is_account_active,
        )
        await new_user_document.insert()
        return _map_user_document_to_entity(new_user_document)

    async def find_user_by_email_address(self, email_address: str) -> RegisteredUserEntity | None:
        """Return the user with the given email address, or None if no such user exists."""
        found_user_document = await RegisteredUserDocument.find_one(
            RegisteredUserDocument.email_address == email_address
        )
        return _map_user_document_to_entity(found_user_document) if found_user_document else None

    async def find_user_by_identifier(self, user_identifier: str) -> RegisteredUserEntity | None:
        """Return the user with the given identifier, or None if it does not exist or is invalid."""
        if not PydanticObjectId.is_valid(user_identifier):
            return None

        found_user_document = await RegisteredUserDocument.get(PydanticObjectId(user_identifier))
        return _map_user_document_to_entity(found_user_document) if found_user_document else None
