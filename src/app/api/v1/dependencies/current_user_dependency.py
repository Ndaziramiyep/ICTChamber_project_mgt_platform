"""FastAPI dependency resolving the currently authenticated user from a bearer access token."""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.v1.dependencies.repository_providers import provide_user_repository
from app.api.v1.dependencies.service_providers import provide_security_token_service
from app.core.security_token_service import ACCESS_TOKEN_TYPE_NAME, SecurityTokenService
from app.domain.entities.registered_user_entity import RegisteredUserEntity
from app.domain.exceptions.authentication_exceptions import InvalidCredentialsError
from app.domain.repositories.user_repository_interface import UserRepositoryInterface

_bearer_token_security_scheme = HTTPBearer()


async def get_current_authenticated_user(
    bearer_credentials: HTTPAuthorizationCredentials = Depends(_bearer_token_security_scheme),
    user_repository: UserRepositoryInterface = Depends(provide_user_repository),
    security_token_service: SecurityTokenService = Depends(provide_security_token_service),
) -> RegisteredUserEntity:
    """Decode the bearer access token and return the authenticated user entity it identifies."""
    decoded_token_payload = security_token_service.decode_and_validate_token(
        bearer_credentials.credentials, expected_token_type_name=ACCESS_TOKEN_TYPE_NAME
    )

    matching_user = await user_repository.find_user_by_identifier(
        decoded_token_payload.subject_user_identifier
    )
    if matching_user is None or not matching_user.is_account_active:
        raise InvalidCredentialsError("The authenticated user account no longer exists.")

    return matching_user
