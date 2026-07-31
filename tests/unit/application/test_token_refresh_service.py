"""Unit tests for TokenRefreshService, with the user repository faked via pytest-mock."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from app.application.services.token_refresh_service import TokenRefreshService
from app.core.security_token_service import SecurityTokenService
from app.domain.exceptions.authentication_exceptions import InvalidCredentialsError
from app.domain.repositories.user_repository_interface import UserRepositoryInterface
from tests.factories.user_factory import build_registered_user_entity


@pytest.fixture
def fake_user_repository(mocker: MockerFixture) -> AsyncMock:
    """Return an autospecced fake of UserRepositoryInterface for isolated unit testing."""
    return mocker.create_autospec(UserRepositoryInterface, instance=True)


@pytest.fixture
def security_token_service() -> SecurityTokenService:
    """Return a real SecurityTokenService configured with test-friendly settings."""
    return SecurityTokenService(
        jwt_secret_key="unit-test-secret-key",
        access_token_expiry_minutes=15,
        refresh_token_expiry_days=7,
    )


class TestIssueNewAccessTokenFromRefreshToken:
    """Behavior of TokenRefreshService.issue_new_access_token_from_refresh_token."""

    async def test_returns_a_new_access_token_for_a_valid_refresh_token(
        self, fake_user_repository: AsyncMock, security_token_service: SecurityTokenService
    ) -> None:
        registered_user_entity = build_registered_user_entity(user_identifier="user-abc-123")
        fake_user_repository.find_user_by_identifier.return_value = registered_user_entity
        refresh_token_value = security_token_service.generate_refresh_token_for_user("user-abc-123")
        token_refresh_service = TokenRefreshService(
            user_repository=fake_user_repository, security_token_service=security_token_service
        )

        new_access_token_value = (
            await token_refresh_service.issue_new_access_token_from_refresh_token(
                refresh_token_value
            )
        )

        assert new_access_token_value
        assert new_access_token_value != refresh_token_value

    async def test_raises_invalid_credentials_error_when_the_user_no_longer_exists(
        self, fake_user_repository: AsyncMock, security_token_service: SecurityTokenService
    ) -> None:
        fake_user_repository.find_user_by_identifier.return_value = None
        refresh_token_value = security_token_service.generate_refresh_token_for_user("user-abc-123")
        token_refresh_service = TokenRefreshService(
            user_repository=fake_user_repository, security_token_service=security_token_service
        )

        with pytest.raises(InvalidCredentialsError):
            await token_refresh_service.issue_new_access_token_from_refresh_token(
                refresh_token_value
            )

    async def test_raises_invalid_credentials_error_when_the_account_is_deactivated(
        self, fake_user_repository: AsyncMock, security_token_service: SecurityTokenService
    ) -> None:
        deactivated_user_entity = build_registered_user_entity(
            user_identifier="user-abc-123", is_account_active=False
        )
        fake_user_repository.find_user_by_identifier.return_value = deactivated_user_entity
        refresh_token_value = security_token_service.generate_refresh_token_for_user("user-abc-123")
        token_refresh_service = TokenRefreshService(
            user_repository=fake_user_repository, security_token_service=security_token_service
        )

        with pytest.raises(InvalidCredentialsError):
            await token_refresh_service.issue_new_access_token_from_refresh_token(
                refresh_token_value
            )
