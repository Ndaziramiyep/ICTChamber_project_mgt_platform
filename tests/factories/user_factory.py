"""Factory functions building test payloads and entities for registered users."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.security_password_hashing import hash_plain_text_password
from app.domain.entities.registered_user_entity import RegisteredUserEntity


def build_registered_user_entity(
    user_identifier: str = "60c72b2f9b1e8b3f1c8e4d1a",
    email_address: str = "jane.doe@example.com",
    plain_text_password: str = "correct-horse-battery-staple",
    display_name: str = "Jane Doe",
    is_account_active: bool = True,
) -> RegisteredUserEntity:
    """Build a RegisteredUserEntity suitable for use in unit and integration tests."""
    return RegisteredUserEntity(
        user_identifier=user_identifier,
        email_address=email_address,
        hashed_password_value=hash_plain_text_password(plain_text_password),
        display_name=display_name,
        account_created_at=datetime.now(UTC),
        is_account_active=is_account_active,
    )


def build_user_registration_request_payload(
    email_address: str = "jane.doe@example.com",
    plain_text_password: str = "correct-horse-battery-staple",
    display_name: str = "Jane Doe",
) -> dict[str, str]:
    """Build a JSON-serializable registration request payload for API integration tests."""
    return {
        "email_address": email_address,
        "plain_text_password": plain_text_password,
        "display_name": display_name,
    }
