"""Domain entity representing a registered user account."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class RegisteredUserEntity:
    """A user who has registered an account with the platform."""

    user_identifier: str
    email_address: str
    hashed_password_value: str
    display_name: str
    account_created_at: datetime
    is_account_active: bool = True
