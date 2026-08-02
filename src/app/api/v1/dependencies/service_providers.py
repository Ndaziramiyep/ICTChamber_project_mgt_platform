"""FastAPI dependency providers supplying constructed application services."""

from __future__ import annotations

from fastapi import Depends

from app.api.v1.dependencies.repository_providers import (
    provide_board_repository,
    provide_column_repository,
    provide_task_repository,
    provide_user_repository,
)
from app.application.services.board_management_service import BoardManagementService
from app.application.services.column_management_service import ColumnManagementService
from app.application.services.task_management_service import TaskManagementService
from app.application.services.token_refresh_service import TokenRefreshService
from app.application.services.user_authentication_service import UserAuthenticationService
from app.application.services.user_registration_service import UserRegistrationService
from app.core.application_settings import ApplicationSettings, get_cached_application_settings
from app.core.security_token_service import SecurityTokenService
from app.domain.repositories.board_repository_interface import BoardRepositoryInterface
from app.domain.repositories.column_repository_interface import ColumnRepositoryInterface
from app.domain.repositories.task_repository_interface import TaskRepositoryInterface
from app.domain.repositories.user_repository_interface import UserRepositoryInterface


def provide_security_token_service(
    application_settings: ApplicationSettings = Depends(get_cached_application_settings),
) -> SecurityTokenService:
    """Supply a SecurityTokenService configured from the current application settings."""
    return SecurityTokenService(
        jwt_secret_key=application_settings.jwt_secret_key,
        access_token_expiry_minutes=application_settings.jwt_access_token_expiry_minutes,
        refresh_token_expiry_days=application_settings.jwt_refresh_token_expiry_days,
    )


def provide_user_registration_service(
    user_repository: UserRepositoryInterface = Depends(provide_user_repository),
) -> UserRegistrationService:
    """Construct the user registration service with its injected repository dependency."""
    return UserRegistrationService(user_repository=user_repository)


def provide_user_authentication_service(
    user_repository: UserRepositoryInterface = Depends(provide_user_repository),
    security_token_service: SecurityTokenService = Depends(provide_security_token_service),
) -> UserAuthenticationService:
    """Construct the user authentication service with its injected dependencies."""
    return UserAuthenticationService(
        user_repository=user_repository, security_token_service=security_token_service
    )


def provide_token_refresh_service(
    user_repository: UserRepositoryInterface = Depends(provide_user_repository),
    security_token_service: SecurityTokenService = Depends(provide_security_token_service),
) -> TokenRefreshService:
    """Construct the token refresh service with its injected dependencies."""
    return TokenRefreshService(
        user_repository=user_repository, security_token_service=security_token_service
    )


def provide_board_management_service(
    board_repository: BoardRepositoryInterface = Depends(provide_board_repository),
) -> BoardManagementService:
    """Construct the board management service with its injected repository dependency."""
    return BoardManagementService(board_repository=board_repository)


def provide_column_management_service(
    column_repository: ColumnRepositoryInterface = Depends(provide_column_repository),
    board_repository: BoardRepositoryInterface = Depends(provide_board_repository),
    task_repository: TaskRepositoryInterface = Depends(provide_task_repository),
) -> ColumnManagementService:
    """Construct the column management service with its injected repository dependencies."""
    return ColumnManagementService(
        column_repository=column_repository,
        board_repository=board_repository,
        task_repository=task_repository,
    )


def provide_task_management_service(
    task_repository: TaskRepositoryInterface = Depends(provide_task_repository),
    column_repository: ColumnRepositoryInterface = Depends(provide_column_repository),
    board_repository: BoardRepositoryInterface = Depends(provide_board_repository),
) -> TaskManagementService:
    """Construct the task management service with its injected repository dependencies."""
    return TaskManagementService(
        task_repository=task_repository,
        column_repository=column_repository,
        board_repository=board_repository,
    )
