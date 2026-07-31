"""Use case for authenticating a user and issuing a JWT access/refresh token pair."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.security_password_hashing import verify_password_against_hash
from app.core.security_token_service import SecurityTokenService
from app.domain.exceptions.authentication_exceptions import InvalidCredentialsError
from app.domain.repositories.user_repository_interface import UserRepositoryInterface


@dataclass
class IssuedTokenPair:
    """An access token and refresh token issued together at login."""

    access_token_value: str
    refresh_token_value: str


class UserAuthenticationService:
    """Authenticates user credentials and issues access/refresh token pairs."""

    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        security_token_service: SecurityTokenService,
    ) -> None:
        """Store the repository used to look up accounts and the service used to issue tokens."""
        self._user_repository = user_repository
        self._security_token_service = security_token_service

    async def authenticate_user_credentials(
        self, email_address: str, plain_text_password: str
    ) -> IssuedTokenPair:
        """Verify the given credentials and return a freshly issued access/refresh token pair."""
        matching_user = await self._user_repository.find_user_by_email_address(email_address)
        if matching_user is None or not verify_password_against_hash(
            plain_text_password, matching_user.hashed_password_value
        ):
            raise InvalidCredentialsError("The provided email address or password is incorrect.")

        return IssuedTokenPair(
            access_token_value=self._security_token_service.generate_access_token_for_user(
                matching_user.user_identifier
            ),
            refresh_token_value=self._security_token_service.generate_refresh_token_for_user(
                matching_user.user_identifier
            ),
        )
