"""Password hashing utilities backed by the Argon2id algorithm."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_argon2_password_hasher = PasswordHasher()


def hash_plain_text_password(plain_text_password: str) -> str:
    """Return an Argon2id hash of the given plain-text password."""
    return _argon2_password_hasher.hash(plain_text_password)


def verify_password_against_hash(plain_text_password: str, hashed_password_value: str) -> bool:
    """Return whether the given plain-text password matches the given Argon2id hash."""
    try:
        return _argon2_password_hasher.verify(hashed_password_value, plain_text_password)
    except VerifyMismatchError:
        return False
