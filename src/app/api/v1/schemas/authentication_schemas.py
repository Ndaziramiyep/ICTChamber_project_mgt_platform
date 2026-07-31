"""Request and response schemas for the authentication endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegistrationRequestSchema(BaseModel):
    """Payload required to register a new user account."""

    email_address: EmailStr
    plain_text_password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)


class UserLoginRequestSchema(BaseModel):
    """Payload required to authenticate an existing user account."""

    email_address: EmailStr
    plain_text_password: str


class TokenRefreshRequestSchema(BaseModel):
    """Payload required to exchange a refresh token for a new access token."""

    refresh_token_value: str


class UserProfileResponseSchema(BaseModel):
    """Public profile information returned for a registered user."""

    user_identifier: str
    email_address: EmailStr
    display_name: str
    account_created_at: datetime
    is_account_active: bool


class TokenPairResponseSchema(BaseModel):
    """Access and refresh token pair returned after a successful login."""

    access_token_value: str
    refresh_token_value: str
    token_type_name: str = "bearer"


class AccessTokenResponseSchema(BaseModel):
    """A freshly issued access token returned by the refresh endpoint."""

    access_token_value: str
    token_type_name: str = "bearer"
