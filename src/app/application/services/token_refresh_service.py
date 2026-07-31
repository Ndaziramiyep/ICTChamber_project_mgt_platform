"""Use case for exchanging a valid refresh token for a new access token."""

from __future__ import annotations

from app.core.security_token_service import REFRESH_TOKEN_TYPE_NAME, SecurityTokenService
from app.domain.exceptions.authentication_exceptions import InvalidCredentialsError
from app.domain.repositories.user_repository_interface import UserRepositoryInterface


class TokenRefreshService:
    """Issues a new access token given a valid, non-expired refresh token."""

    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        security_token_service: SecurityTokenService,
    ) -> None:
        """Store the repository used to confirm the user still exists and the token service."""
        self._user_repository = user_repository
        self._security_token_service = security_token_service

    async def issue_new_access_token_from_refresh_token(self, refresh_token_value: str) -> str:
        """Validate the given refresh token and return a freshly issued access token."""
        decoded_token_payload = self._security_token_service.decode_and_validate_token(
            refresh_token_value, expected_token_type_name=REFRESH_TOKEN_TYPE_NAME
        )

        matching_user = await self._user_repository.find_user_by_identifier(
            decoded_token_payload.subject_user_identifier
        )
        if matching_user is None or not matching_user.is_account_active:
            raise InvalidCredentialsError(
                "The account associated with this token no longer exists."
            )

        return self._security_token_service.generate_access_token_for_user(
            matching_user.user_identifier
        )
