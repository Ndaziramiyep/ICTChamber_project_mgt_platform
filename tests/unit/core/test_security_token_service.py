"""Unit tests for JWT access and refresh token issuance and verification."""

from __future__ import annotations

import time

import pytest

from app.core.security_token_service import (
    ACCESS_TOKEN_TYPE_NAME,
    REFRESH_TOKEN_TYPE_NAME,
    SecurityTokenService,
)
from app.domain.exceptions.authentication_exceptions import (
    ExpiredTokenError,
    InvalidTokenTypeError,
    MalformedTokenError,
)


@pytest.fixture
def security_token_service() -> SecurityTokenService:
    """Return a SecurityTokenService configured with short, test-friendly expiries."""
    return SecurityTokenService(
        jwt_secret_key="unit-test-secret-key",
        access_token_expiry_minutes=15,
        refresh_token_expiry_days=7,
    )


class TestGenerateAndDecodeAccessToken:
    """Round-trip behavior for access tokens."""

    def test_decode_and_validate_token_returns_the_original_subject(
        self, security_token_service: SecurityTokenService
    ) -> None:
        access_token_value = security_token_service.generate_access_token_for_user("user-123")

        decoded_token_payload = security_token_service.decode_and_validate_token(
            access_token_value, expected_token_type_name=ACCESS_TOKEN_TYPE_NAME
        )

        assert decoded_token_payload.subject_user_identifier == "user-123"
        assert decoded_token_payload.token_type_name == ACCESS_TOKEN_TYPE_NAME

    def test_decode_and_validate_token_rejects_a_refresh_token_as_access(
        self, security_token_service: SecurityTokenService
    ) -> None:
        refresh_token_value = security_token_service.generate_refresh_token_for_user("user-123")

        with pytest.raises(InvalidTokenTypeError):
            security_token_service.decode_and_validate_token(
                refresh_token_value, expected_token_type_name=ACCESS_TOKEN_TYPE_NAME
            )

    def test_decode_and_validate_token_rejects_a_malformed_token(
        self, security_token_service: SecurityTokenService
    ) -> None:
        with pytest.raises(MalformedTokenError):
            security_token_service.decode_and_validate_token(
                "not-a-real-jwt", expected_token_type_name=ACCESS_TOKEN_TYPE_NAME
            )

    def test_decode_and_validate_token_rejects_an_expired_token(self) -> None:
        immediately_expiring_token_service = SecurityTokenService(
            jwt_secret_key="unit-test-secret-key",
            access_token_expiry_minutes=0,
            refresh_token_expiry_days=0,
        )
        access_token_value = immediately_expiring_token_service.generate_access_token_for_user(
            "user-123"
        )
        time.sleep(1)

        with pytest.raises(ExpiredTokenError):
            immediately_expiring_token_service.decode_and_validate_token(
                access_token_value, expected_token_type_name=ACCESS_TOKEN_TYPE_NAME
            )


class TestGenerateAndDecodeRefreshToken:
    """Round-trip behavior for refresh tokens."""

    def test_decode_and_validate_token_returns_the_original_subject(
        self, security_token_service: SecurityTokenService
    ) -> None:
        refresh_token_value = security_token_service.generate_refresh_token_for_user("user-456")

        decoded_token_payload = security_token_service.decode_and_validate_token(
            refresh_token_value, expected_token_type_name=REFRESH_TOKEN_TYPE_NAME
        )

        assert decoded_token_payload.subject_user_identifier == "user-456"
        assert decoded_token_payload.token_type_name == REFRESH_TOKEN_TYPE_NAME
