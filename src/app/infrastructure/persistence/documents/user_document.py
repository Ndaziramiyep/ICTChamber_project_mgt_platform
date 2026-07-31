"""Beanie document schema for the user account collection."""

from __future__ import annotations

from datetime import UTC, datetime

from beanie import Document, Indexed
from pydantic import Field


class RegisteredUserDocument(Document):
    """MongoDB document persisting a registered user account."""

    email_address: Indexed(str, unique=True)  # type: ignore[valid-type]
    hashed_password_value: str
    display_name: str
    account_created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_account_active: bool = True

    class Settings:
        """Beanie collection configuration for registered user documents."""

        name = "registered_users"
