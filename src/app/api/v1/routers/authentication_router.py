"""HTTP routes for user registration, login, token refresh, and profile retrieval."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies.current_user_dependency import get_current_authenticated_user
from app.api.v1.dependencies.service_providers import (
    provide_token_refresh_service,
    provide_user_authentication_service,
    provide_user_registration_service,
)
from app.api.v1.schemas.authentication_schemas import (
    AccessTokenResponseSchema,
    TokenPairResponseSchema,
    TokenRefreshRequestSchema,
    UserLoginRequestSchema,
    UserProfileResponseSchema,
    UserRegistrationRequestSchema,
)
from app.application.services.token_refresh_service import TokenRefreshService
from app.application.services.user_authentication_service import UserAuthenticationService
from app.application.services.user_registration_service import UserRegistrationService
from app.domain.entities.registered_user_entity import RegisteredUserEntity

authentication_router = APIRouter(prefix="/auth", tags=["authentication"])


def _map_user_entity_to_profile_response(
    user_entity: RegisteredUserEntity,
) -> UserProfileResponseSchema:
    """Convert a RegisteredUserEntity into its public HTTP profile representation."""
    return UserProfileResponseSchema(
        user_identifier=user_entity.user_identifier,
        email_address=user_entity.email_address,
        display_name=user_entity.display_name,
        account_created_at=user_entity.account_created_at,
        is_account_active=user_entity.is_account_active,
    )


@authentication_router.post(
    "/register",
    response_model=UserProfileResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register_new_user_account(
    registration_request: UserRegistrationRequestSchema,
    user_registration_service: UserRegistrationService = Depends(provide_user_registration_service),
) -> UserProfileResponseSchema:
    """Register a new user account and return its public profile."""
    created_user_entity = await user_registration_service.register_new_user_account(
        email_address=registration_request.email_address,
        plain_text_password=registration_request.plain_text_password,
        display_name=registration_request.display_name,
    )
    return _map_user_entity_to_profile_response(created_user_entity)


@authentication_router.post("/login", response_model=TokenPairResponseSchema)
async def authenticate_user_and_issue_tokens(
    login_request: UserLoginRequestSchema,
    user_authentication_service: UserAuthenticationService = Depends(
        provide_user_authentication_service
    ),
) -> TokenPairResponseSchema:
    """Authenticate the given credentials and return a fresh access/refresh token pair."""
    issued_token_pair = await user_authentication_service.authenticate_user_credentials(
        email_address=login_request.email_address,
        plain_text_password=login_request.plain_text_password,
    )
    return TokenPairResponseSchema(
        access_token_value=issued_token_pair.access_token_value,
        refresh_token_value=issued_token_pair.refresh_token_value,
    )


@authentication_router.post("/refresh", response_model=AccessTokenResponseSchema)
async def refresh_access_token(
    refresh_request: TokenRefreshRequestSchema,
    token_refresh_service: TokenRefreshService = Depends(provide_token_refresh_service),
) -> AccessTokenResponseSchema:
    """Exchange a valid refresh token for a freshly issued access token."""
    new_access_token_value = await token_refresh_service.issue_new_access_token_from_refresh_token(
        refresh_request.refresh_token_value
    )
    return AccessTokenResponseSchema(access_token_value=new_access_token_value)


@authentication_router.get("/me", response_model=UserProfileResponseSchema)
async def get_authenticated_user_profile(
    current_authenticated_user: RegisteredUserEntity = Depends(get_current_authenticated_user),
) -> UserProfileResponseSchema:
    """Return the profile of the currently authenticated user."""
    return _map_user_entity_to_profile_response(current_authenticated_user)
