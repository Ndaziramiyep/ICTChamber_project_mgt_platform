"""Unit tests for UserAuthenticationService, with the user repository faked via pytest-mock."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from app.application.services.user_authentication_service import UserAuthenticationService
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


class TestAuthenticateUserCredentials:
    """Behavior of UserAuthenticationService.authenticate_user_credentials."""

    async def test_issues_an_access_and_refresh_token_pair_for_correct_credentials(
        self, fake_user_repository: AsyncMock, security_token_service: SecurityTokenService
    ) -> None:
        registered_user_entity = build_registered_user_entity(
            email_address="jane.doe@example.com",
            plain_text_password="correct-horse-battery-staple",
        )
        fake_user_repository.find_user_by_email_address.return_value = registered_user_entity
        user_authentication_service = UserAuthenticationService(
            user_repository=fake_user_repository, security_token_service=security_token_service
        )

        issued_token_pair = await user_authentication_service.authenticate_user_credentials(
            email_address="jane.doe@example.com",
            plain_text_password="correct-horse-battery-staple",
        )

        assert issued_token_pair.access_token_value
        assert issued_token_pair.refresh_token_value
        assert issued_token_pair.access_token_value != issued_token_pair.refresh_token_value

    async def test_raises_invalid_credentials_error_for_an_unknown_email_address(
        self, fake_user_repository: AsyncMock, security_token_service: SecurityTokenService
    ) -> None:
        fake_user_repository.find_user_by_email_address.return_value = None
        user_authentication_service = UserAuthenticationService(
            user_repository=fake_user_repository, security_token_service=security_token_service
        )

        with pytest.raises(InvalidCredentialsError):
            await user_authentication_service.authenticate_user_credentials(
                email_address="unknown@example.com",
                plain_text_password="whatever-password",
            )

    async def test_raises_invalid_credentials_error_for_an_incorrect_password(
        self, fake_user_repository: AsyncMock, security_token_service: SecurityTokenService
    ) -> None:
        registered_user_entity = build_registered_user_entity(
            email_address="jane.doe@example.com",
            plain_text_password="correct-horse-battery-staple",
        )
        fake_user_repository.find_user_by_email_address.return_value = registered_user_entity
        user_authentication_service = UserAuthenticationService(
            user_repository=fake_user_repository, security_token_service=security_token_service
        )

        with pytest.raises(InvalidCredentialsError):
            await user_authentication_service.authenticate_user_credentials(
                email_address="jane.doe@example.com",
                plain_text_password="wrong-password-value",
            )
