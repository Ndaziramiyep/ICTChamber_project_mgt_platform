"""Unit tests for UserRegistrationService, with the user repository faked via pytest-mock."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from app.application.services.user_registration_service import UserRegistrationService
from app.domain.exceptions.authentication_exceptions import EmailAddressAlreadyRegisteredError
from app.domain.repositories.user_repository_interface import UserRepositoryInterface
from tests.factories.user_factory import build_registered_user_entity


@pytest.fixture
def fake_user_repository(mocker: MockerFixture) -> AsyncMock:
    """Return an autospecced fake of UserRepositoryInterface for isolated unit testing."""
    return mocker.create_autospec(UserRepositoryInterface, instance=True)


class TestRegisterNewUserAccount:
    """Behavior of UserRegistrationService.register_new_user_account."""

    async def test_persists_a_new_user_when_email_address_is_not_already_registered(
        self, fake_user_repository: AsyncMock
    ) -> None:
        fake_user_repository.find_user_by_email_address.return_value = None
        fake_user_repository.create_user_record.return_value = build_registered_user_entity(
            email_address="new.user@example.com"
        )
        user_registration_service = UserRegistrationService(user_repository=fake_user_repository)

        created_user_entity = await user_registration_service.register_new_user_account(
            email_address="new.user@example.com",
            plain_text_password="correct-horse-battery-staple",
            display_name="New User",
        )

        assert created_user_entity.email_address == "new.user@example.com"
        fake_user_repository.create_user_record.assert_awaited_once()

    async def test_hashes_the_plain_text_password_before_persisting(
        self, fake_user_repository: AsyncMock
    ) -> None:
        fake_user_repository.find_user_by_email_address.return_value = None
        fake_user_repository.create_user_record.side_effect = lambda user_entity: user_entity
        user_registration_service = UserRegistrationService(user_repository=fake_user_repository)

        created_user_entity = await user_registration_service.register_new_user_account(
            email_address="new.user@example.com",
            plain_text_password="correct-horse-battery-staple",
            display_name="New User",
        )

        assert created_user_entity.hashed_password_value != "correct-horse-battery-staple"

    async def test_raises_email_already_registered_error_for_a_duplicate_email_address(
        self, fake_user_repository: AsyncMock
    ) -> None:
        fake_user_repository.find_user_by_email_address.return_value = build_registered_user_entity(
            email_address="existing.user@example.com"
        )
        user_registration_service = UserRegistrationService(user_repository=fake_user_repository)

        with pytest.raises(EmailAddressAlreadyRegisteredError):
            await user_registration_service.register_new_user_account(
                email_address="existing.user@example.com",
                plain_text_password="correct-horse-battery-staple",
                display_name="Existing User",
            )

        fake_user_repository.create_user_record.assert_not_awaited()
