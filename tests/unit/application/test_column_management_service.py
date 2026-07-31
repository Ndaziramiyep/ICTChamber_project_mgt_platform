"""Unit tests for ColumnManagementService, with repositories faked via pytest-mock."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from app.application.services.column_management_service import ColumnManagementService
from app.domain.exceptions.board_domain_exceptions import (
    BoardNotFoundError,
    UnauthorizedBoardAccessError,
)
from app.domain.exceptions.column_domain_exceptions import ColumnNotFoundError
from app.domain.repositories.board_repository_interface import BoardRepositoryInterface
from app.domain.repositories.column_repository_interface import ColumnRepositoryInterface
from app.domain.repositories.task_repository_interface import TaskRepositoryInterface
from tests.factories.board_factory import build_project_board_entity
from tests.factories.column_factory import build_board_column_entity

OWNING_USER_IDENTIFIER = "owning-user-123"
OTHER_USER_IDENTIFIER = "other-user-456"
PARENT_BOARD_IDENTIFIER = "board-abc-123"


@pytest.fixture
def fake_column_repository(mocker: MockerFixture) -> AsyncMock:
    """Return an autospecced fake of ColumnRepositoryInterface for isolated unit testing."""
    return mocker.create_autospec(ColumnRepositoryInterface, instance=True)


@pytest.fixture
def fake_board_repository(mocker: MockerFixture) -> AsyncMock:
    """Return an autospecced fake of BoardRepositoryInterface for isolated unit testing."""
    return mocker.create_autospec(BoardRepositoryInterface, instance=True)


@pytest.fixture
def fake_task_repository(mocker: MockerFixture) -> AsyncMock:
    """Return an autospecced fake of TaskRepositoryInterface for isolated unit testing."""
    return mocker.create_autospec(TaskRepositoryInterface, instance=True)


class TestCreateColumnForBoard:
    """Behavior of ColumnManagementService.create_column_for_board."""

    async def test_appends_the_new_column_after_existing_columns(
        self,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
        fake_task_repository: AsyncMock,
    ) -> None:
        fake_board_repository.find_board_by_identifier.return_value = build_project_board_entity(
            board_identifier=PARENT_BOARD_IDENTIFIER, owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        fake_column_repository.find_columns_by_parent_board_identifier.return_value = [
            build_board_column_entity(column_display_order=0),
            build_board_column_entity(column_display_order=1),
        ]
        fake_column_repository.create_column_record.side_effect = (
            lambda column_entity: column_entity
        )
        column_management_service = ColumnManagementService(
            column_repository=fake_column_repository,
            board_repository=fake_board_repository,
            task_repository=fake_task_repository,
        )

        created_column_entity = await column_management_service.create_column_for_board(
            parent_board_identifier=PARENT_BOARD_IDENTIFIER,
            requesting_user_identifier=OWNING_USER_IDENTIFIER,
            column_title="In Progress",
        )

        assert created_column_entity.column_display_order == 2
        assert created_column_entity.column_title == "In Progress"

    async def test_raises_unauthorized_board_access_error_for_a_non_owning_user(
        self,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
        fake_task_repository: AsyncMock,
    ) -> None:
        fake_board_repository.find_board_by_identifier.return_value = build_project_board_entity(
            board_identifier=PARENT_BOARD_IDENTIFIER, owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        column_management_service = ColumnManagementService(
            column_repository=fake_column_repository,
            board_repository=fake_board_repository,
            task_repository=fake_task_repository,
        )

        with pytest.raises(UnauthorizedBoardAccessError):
            await column_management_service.create_column_for_board(
                parent_board_identifier=PARENT_BOARD_IDENTIFIER,
                requesting_user_identifier=OTHER_USER_IDENTIFIER,
                column_title="In Progress",
            )

        fake_column_repository.create_column_record.assert_not_awaited()

    async def test_raises_board_not_found_error_for_an_unknown_board(
        self,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
        fake_task_repository: AsyncMock,
    ) -> None:
        fake_board_repository.find_board_by_identifier.return_value = None
        column_management_service = ColumnManagementService(
            column_repository=fake_column_repository,
            board_repository=fake_board_repository,
            task_repository=fake_task_repository,
        )

        with pytest.raises(BoardNotFoundError):
            await column_management_service.create_column_for_board(
                parent_board_identifier="missing-board-id",
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
                column_title="In Progress",
            )


class TestFindColumnOwnedByAuthenticatedUser:
    """Behavior of ColumnManagementService.find_column_owned_by_authenticated_user."""

    async def test_returns_the_column_when_the_requester_owns_the_parent_board(
        self,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
        fake_task_repository: AsyncMock,
    ) -> None:
        owned_column_entity = build_board_column_entity(
            parent_board_identifier=PARENT_BOARD_IDENTIFIER
        )
        fake_column_repository.find_column_by_identifier.return_value = owned_column_entity
        fake_board_repository.find_board_by_identifier.return_value = build_project_board_entity(
            board_identifier=PARENT_BOARD_IDENTIFIER, owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        column_management_service = ColumnManagementService(
            column_repository=fake_column_repository,
            board_repository=fake_board_repository,
            task_repository=fake_task_repository,
        )

        found_column_entity = (
            await column_management_service.find_column_owned_by_authenticated_user(
                column_identifier=owned_column_entity.column_identifier,
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
            )
        )

        assert found_column_entity is owned_column_entity

    async def test_raises_column_not_found_error_when_no_column_exists(
        self,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
        fake_task_repository: AsyncMock,
    ) -> None:
        fake_column_repository.find_column_by_identifier.return_value = None
        column_management_service = ColumnManagementService(
            column_repository=fake_column_repository,
            board_repository=fake_board_repository,
            task_repository=fake_task_repository,
        )

        with pytest.raises(ColumnNotFoundError):
            await column_management_service.find_column_owned_by_authenticated_user(
                column_identifier="missing-column-id",
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
            )

    async def test_raises_unauthorized_board_access_error_for_a_non_owning_user(
        self,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
        fake_task_repository: AsyncMock,
    ) -> None:
        someone_elses_column_entity = build_board_column_entity(
            parent_board_identifier=PARENT_BOARD_IDENTIFIER
        )
        fake_column_repository.find_column_by_identifier.return_value = someone_elses_column_entity
        fake_board_repository.find_board_by_identifier.return_value = build_project_board_entity(
            board_identifier=PARENT_BOARD_IDENTIFIER, owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        column_management_service = ColumnManagementService(
            column_repository=fake_column_repository,
            board_repository=fake_board_repository,
            task_repository=fake_task_repository,
        )

        with pytest.raises(UnauthorizedBoardAccessError):
            await column_management_service.find_column_owned_by_authenticated_user(
                column_identifier=someone_elses_column_entity.column_identifier,
                requesting_user_identifier=OTHER_USER_IDENTIFIER,
            )


class TestUpdateAndDeleteColumn:
    """Behavior of update_column_owned_by_authenticated_user and
    delete_column_owned_by_authenticated_user."""

    async def test_update_renames_the_column_for_the_owning_user(
        self,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
        fake_task_repository: AsyncMock,
    ) -> None:
        owned_column_entity = build_board_column_entity(
            parent_board_identifier=PARENT_BOARD_IDENTIFIER
        )
        fake_column_repository.find_column_by_identifier.return_value = owned_column_entity
        fake_board_repository.find_board_by_identifier.return_value = build_project_board_entity(
            board_identifier=PARENT_BOARD_IDENTIFIER, owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        fake_column_repository.update_column_record.side_effect = (
            lambda column_entity: column_entity
        )
        column_management_service = ColumnManagementService(
            column_repository=fake_column_repository,
            board_repository=fake_board_repository,
            task_repository=fake_task_repository,
        )

        updated_column_entity = (
            await column_management_service.update_column_owned_by_authenticated_user(
                column_identifier=owned_column_entity.column_identifier,
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
                column_title="Renamed Column",
            )
        )

        assert updated_column_entity.column_title == "Renamed Column"

    async def test_delete_removes_the_column_for_the_owning_user(
        self,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
        fake_task_repository: AsyncMock,
    ) -> None:
        owned_column_entity = build_board_column_entity(
            parent_board_identifier=PARENT_BOARD_IDENTIFIER
        )
        fake_column_repository.find_column_by_identifier.return_value = owned_column_entity
        fake_board_repository.find_board_by_identifier.return_value = build_project_board_entity(
            board_identifier=PARENT_BOARD_IDENTIFIER, owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        column_management_service = ColumnManagementService(
            column_repository=fake_column_repository,
            board_repository=fake_board_repository,
            task_repository=fake_task_repository,
        )

        await column_management_service.delete_column_owned_by_authenticated_user(
            column_identifier=owned_column_entity.column_identifier,
            requesting_user_identifier=OWNING_USER_IDENTIFIER,
        )

        fake_column_repository.delete_column_by_identifier.assert_awaited_once_with(
            owned_column_entity.column_identifier
        )

    async def test_delete_cascades_to_every_task_in_the_column(
        self,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
        fake_task_repository: AsyncMock,
    ) -> None:
        owned_column_entity = build_board_column_entity(
            parent_board_identifier=PARENT_BOARD_IDENTIFIER
        )
        fake_column_repository.find_column_by_identifier.return_value = owned_column_entity
        fake_board_repository.find_board_by_identifier.return_value = build_project_board_entity(
            board_identifier=PARENT_BOARD_IDENTIFIER, owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        column_management_service = ColumnManagementService(
            column_repository=fake_column_repository,
            board_repository=fake_board_repository,
            task_repository=fake_task_repository,
        )

        await column_management_service.delete_column_owned_by_authenticated_user(
            column_identifier=owned_column_entity.column_identifier,
            requesting_user_identifier=OWNING_USER_IDENTIFIER,
        )

        fake_task_repository.delete_tasks_by_parent_column_identifier.assert_awaited_once_with(
            owned_column_entity.column_identifier
        )
