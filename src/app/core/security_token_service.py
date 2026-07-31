"""Issuance and verification of JWT access and refresh tokens."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from app.domain.exceptions.authentication_exceptions import (
    ExpiredTokenError,
    InvalidTokenTypeError,
    MalformedTokenError,
)

ACCESS_TOKEN_TYPE_NAME = "access"
REFRESH_TOKEN_TYPE_NAME = "refresh"

_JWT_SIGNING_ALGORITHM = "HS256"


@dataclass
class DecodedTokenPayload:
    """The claims extracted from a successfully verified JWT."""

    subject_user_identifier: str
    token_type_name: str
    issued_at_timestamp: int
    expires_at_timestamp: int


class SecurityTokenService:
    """Issues and verifies JWT access and refresh tokens for authenticated users."""

    def __init__(
        self,
        jwt_secret_key: str,
        access_token_expiry_minutes: int,
        refresh_token_expiry_days: int,
    ) -> None:
        """Store the signing secret and expiry durations used when issuing tokens."""
        self._jwt_secret_key = jwt_secret_key
        self._access_token_expiry_minutes = access_token_expiry_minutes
        self._refresh_token_expiry_days = refresh_token_expiry_days

    def generate_access_token_for_user(self, user_identifier: str) -> str:
        """Return a short-lived signed access token identifying the given user."""
        return self._encode_token_for_user(
            user_identifier=user_identifier,
            token_type_name=ACCESS_TOKEN_TYPE_NAME,
            token_lifetime=timedelta(minutes=self._access_token_expiry_minutes),
        )

    def generate_refresh_token_for_user(self, user_identifier: str) -> str:
        """Return a long-lived signed refresh token identifying the given user."""
        return self._encode_token_for_user(
            user_identifier=user_identifier,
            token_type_name=REFRESH_TOKEN_TYPE_NAME,
            token_lifetime=timedelta(days=self._refresh_token_expiry_days),
        )

    def decode_and_validate_token(
        self, token_value: str, expected_token_type_name: str
    ) -> DecodedTokenPayload:
        """Decode the token, verify its signature and expiry, and enforce its declared type."""
        try:
            decoded_claims = jwt.decode(
                token_value, self._jwt_secret_key, algorithms=[_JWT_SIGNING_ALGORITHM]
            )
        except jwt.ExpiredSignatureError as expired_signature_error:
            raise ExpiredTokenError("The provided token has expired.") from expired_signature_error
        except jwt.InvalidTokenError as invalid_token_error:
            raise MalformedTokenError(
                "The provided token could not be verified."
            ) from invalid_token_error

        actual_token_type_name = decoded_claims.get("token_type")
        if actual_token_type_name != expected_token_type_name:
            raise InvalidTokenTypeError(
                f"Expected a '{expected_token_type_name}' token but received "
                f"'{actual_token_type_name}'."
            )

        return DecodedTokenPayload(
            subject_user_identifier=decoded_claims["sub"],
            token_type_name=actual_token_type_name,
            issued_at_timestamp=decoded_claims["issued_at_timestamp"],
            expires_at_timestamp=decoded_claims["expires_at_timestamp"],
        )

    def _encode_token_for_user(
        self, user_identifier: str, token_type_name: str, token_lifetime: timedelta
    ) -> str:
        """Build and sign a JWT for the given user, token type, and lifetime."""
        current_utc_moment = datetime.now(UTC)
        expiry_utc_moment = current_utc_moment + token_lifetime

        token_claims = {
            "sub": user_identifier,
            "token_type": token_type_name,
            "issued_at_timestamp": int(current_utc_moment.timestamp()),
            "expires_at_timestamp": int(expiry_utc_moment.timestamp()),
            "exp": expiry_utc_moment,
            "iat": current_utc_moment,
        }

        return jwt.encode(token_claims, self._jwt_secret_key, algorithm=_JWT_SIGNING_ALGORITHM)
