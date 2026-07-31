"""Unit tests for BoardManagementService, with the board repository faked via pytest-mock."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from app.application.services.board_management_service import BoardManagementService
from app.domain.exceptions.board_domain_exceptions import (
    BoardNotFoundError,
    UnauthorizedBoardAccessError,
)
from app.domain.repositories.board_repository_interface import BoardRepositoryInterface
from tests.factories.board_factory import build_project_board_entity

OWNING_USER_IDENTIFIER = "owning-user-123"
OTHER_USER_IDENTIFIER = "other-user-456"


@pytest.fixture
def fake_board_repository(mocker: MockerFixture) -> AsyncMock:
    """Return an autospecced fake of BoardRepositoryInterface for isolated unit testing."""
    return mocker.create_autospec(BoardRepositoryInterface, instance=True)


class TestCreateBoardForAuthenticatedUser:
    """Behavior of BoardManagementService.create_board_for_authenticated_user."""

    async def test_persists_a_new_board_owned_by_the_given_user(
        self, fake_board_repository: AsyncMock
    ) -> None:
        fake_board_repository.create_board_record.side_effect = lambda board_entity: board_entity
        board_management_service = BoardManagementService(board_repository=fake_board_repository)

        created_board_entity = await board_management_service.create_board_for_authenticated_user(
            owning_user_identifier=OWNING_USER_IDENTIFIER,
            board_title="New Board",
            board_description=None,
        )

        assert created_board_entity.owning_user_identifier == OWNING_USER_IDENTIFIER
        assert created_board_entity.board_title == "New Board"


class TestFindBoardOwnedByAuthenticatedUser:
    """Behavior of BoardManagementService.find_board_owned_by_authenticated_user."""

    async def test_returns_the_board_when_the_requester_owns_it(
        self, fake_board_repository: AsyncMock
    ) -> None:
        owned_board_entity = build_project_board_entity(
            owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        fake_board_repository.find_board_by_identifier.return_value = owned_board_entity
        board_management_service = BoardManagementService(board_repository=fake_board_repository)

        found_board_entity = await board_management_service.find_board_owned_by_authenticated_user(
            board_identifier=owned_board_entity.board_identifier,
            requesting_user_identifier=OWNING_USER_IDENTIFIER,
        )

        assert found_board_entity is owned_board_entity

    async def test_raises_board_not_found_error_when_no_board_exists(
        self, fake_board_repository: AsyncMock
    ) -> None:
        fake_board_repository.find_board_by_identifier.return_value = None
        board_management_service = BoardManagementService(board_repository=fake_board_repository)

        with pytest.raises(BoardNotFoundError):
            await board_management_service.find_board_owned_by_authenticated_user(
                board_identifier="missing-board-id",
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
            )

    async def test_raises_unauthorized_board_access_error_for_a_non_owning_user(
        self, fake_board_repository: AsyncMock
    ) -> None:
        someone_elses_board_entity = build_project_board_entity(
            owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        fake_board_repository.find_board_by_identifier.return_value = someone_elses_board_entity
        board_management_service = BoardManagementService(board_repository=fake_board_repository)

        with pytest.raises(UnauthorizedBoardAccessError):
            await board_management_service.find_board_owned_by_authenticated_user(
                board_identifier=someone_elses_board_entity.board_identifier,
                requesting_user_identifier=OTHER_USER_IDENTIFIER,
            )


class TestUpdateBoardOwnedByAuthenticatedUser:
    """Behavior of BoardManagementService.update_board_owned_by_authenticated_user."""

    async def test_updates_title_and_description_for_the_owning_user(
        self, fake_board_repository: AsyncMock
    ) -> None:
        owned_board_entity = build_project_board_entity(
            owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        fake_board_repository.find_board_by_identifier.return_value = owned_board_entity
        fake_board_repository.update_board_record.side_effect = lambda board_entity: board_entity
        board_management_service = BoardManagementService(board_repository=fake_board_repository)

        updated_board_entity = (
            await board_management_service.update_board_owned_by_authenticated_user(
                board_identifier=owned_board_entity.board_identifier,
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
                board_title="Renamed Board",
                board_description="Updated description",
            )
        )

        assert updated_board_entity.board_title == "Renamed Board"
        assert updated_board_entity.board_description == "Updated description"

    async def test_raises_unauthorized_board_access_error_for_a_non_owning_user(
        self, fake_board_repository: AsyncMock
    ) -> None:
        someone_elses_board_entity = build_project_board_entity(
            owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        fake_board_repository.find_board_by_identifier.return_value = someone_elses_board_entity
        board_management_service = BoardManagementService(board_repository=fake_board_repository)

        with pytest.raises(UnauthorizedBoardAccessError):
            await board_management_service.update_board_owned_by_authenticated_user(
                board_identifier=someone_elses_board_entity.board_identifier,
                requesting_user_identifier=OTHER_USER_IDENTIFIER,
                board_title="Renamed Board",
                board_description=None,
            )

        fake_board_repository.update_board_record.assert_not_awaited()


class TestDeleteBoardOwnedByAuthenticatedUser:
    """Behavior of BoardManagementService.delete_board_owned_by_authenticated_user."""

    async def test_deletes_the_board_when_owned_by_the_requester(
        self, fake_board_repository: AsyncMock
    ) -> None:
        owned_board_entity = build_project_board_entity(
            owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        fake_board_repository.find_board_by_identifier.return_value = owned_board_entity
        board_management_service = BoardManagementService(board_repository=fake_board_repository)

        await board_management_service.delete_board_owned_by_authenticated_user(
            board_identifier=owned_board_entity.board_identifier,
            requesting_user_identifier=OWNING_USER_IDENTIFIER,
        )

        fake_board_repository.delete_board_by_identifier.assert_awaited_once_with(
            owned_board_entity.board_identifier
        )

    async def test_raises_unauthorized_board_access_error_for_a_non_owning_user(
        self, fake_board_repository: AsyncMock
    ) -> None:
        someone_elses_board_entity = build_project_board_entity(
            owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        fake_board_repository.find_board_by_identifier.return_value = someone_elses_board_entity
        board_management_service = BoardManagementService(board_repository=fake_board_repository)

        with pytest.raises(UnauthorizedBoardAccessError):
            await board_management_service.delete_board_owned_by_authenticated_user(
                board_identifier=someone_elses_board_entity.board_identifier,
                requesting_user_identifier=OTHER_USER_IDENTIFIER,
            )

        fake_board_repository.delete_board_by_identifier.assert_not_awaited()
