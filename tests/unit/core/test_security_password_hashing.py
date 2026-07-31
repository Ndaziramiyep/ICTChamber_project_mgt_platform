"""Unit tests for the Argon2-backed password hashing utilities."""

from __future__ import annotations

from app.core.security_password_hashing import (
    hash_plain_text_password,
    verify_password_against_hash,
)


class TestHashAndVerifyPassword:
    """Round-trip and mismatch behavior for password hashing."""

    def test_hash_plain_text_password_does_not_return_the_plain_text_value(self) -> None:
        hashed_password_value = hash_plain_text_password("correct-horse-battery-staple")

        assert hashed_password_value != "correct-horse-battery-staple"

    def test_verify_password_against_hash_accepts_the_correct_password(self) -> None:
        hashed_password_value = hash_plain_text_password("correct-horse-battery-staple")

        assert (
            verify_password_against_hash("correct-horse-battery-staple", hashed_password_value)
            is True
        )

    def test_verify_password_against_hash_rejects_an_incorrect_password(self) -> None:
        hashed_password_value = hash_plain_text_password("correct-horse-battery-staple")

        assert verify_password_against_hash("wrong-password-value", hashed_password_value) is False
