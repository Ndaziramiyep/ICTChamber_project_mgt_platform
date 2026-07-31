"""Unit tests for TaskManagementService, with repositories faked via pytest-mock."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from app.application.services.task_management_service import TaskManagementService
from app.domain.exceptions.board_domain_exceptions import UnauthorizedBoardAccessError
from app.domain.exceptions.column_domain_exceptions import ColumnNotFoundError
from app.domain.exceptions.task_domain_exceptions import TaskNotFoundError
from app.domain.repositories.board_repository_interface import BoardRepositoryInterface
from app.domain.repositories.column_repository_interface import ColumnRepositoryInterface
from app.domain.repositories.task_repository_interface import TaskRepositoryInterface
from app.domain.value_objects.task_position_value import DEFAULT_POSITION_GAP
from tests.factories.board_factory import build_project_board_entity
from tests.factories.column_factory import build_board_column_entity
from tests.factories.task_factory import build_kanban_task_entity

OWNING_USER_IDENTIFIER = "owning-user-123"
OTHER_USER_IDENTIFIER = "other-user-456"
PARENT_BOARD_IDENTIFIER = "board-abc-123"
PARENT_COLUMN_IDENTIFIER = "column-def-456"


@pytest.fixture
def fake_task_repository(mocker: MockerFixture) -> AsyncMock:
    """Return an autospecced fake of TaskRepositoryInterface for isolated unit testing."""
    return mocker.create_autospec(TaskRepositoryInterface, instance=True)


@pytest.fixture
def fake_column_repository(mocker: MockerFixture) -> AsyncMock:
    """Return an autospecced fake of ColumnRepositoryInterface for isolated unit testing."""
    return mocker.create_autospec(ColumnRepositoryInterface, instance=True)


@pytest.fixture
def fake_board_repository(mocker: MockerFixture) -> AsyncMock:
    """Return an autospecced fake of BoardRepositoryInterface for isolated unit testing."""
    return mocker.create_autospec(BoardRepositoryInterface, instance=True)


@pytest.fixture
def task_management_service(
    fake_task_repository: AsyncMock,
    fake_column_repository: AsyncMock,
    fake_board_repository: AsyncMock,
) -> TaskManagementService:
    """Return a TaskManagementService wired with autospecced fake repositories."""
    return TaskManagementService(
        task_repository=fake_task_repository,
        column_repository=fake_column_repository,
        board_repository=fake_board_repository,
    )


def _stub_owned_column(fake_column_repository: AsyncMock, fake_board_repository: AsyncMock) -> None:
    """Configure the fakes so PARENT_COLUMN_IDENTIFIER resolves to a column owned by the user."""
    fake_column_repository.find_column_by_identifier.return_value = build_board_column_entity(
        column_identifier=PARENT_COLUMN_IDENTIFIER, parent_board_identifier=PARENT_BOARD_IDENTIFIER
    )
    fake_board_repository.find_board_by_identifier.return_value = build_project_board_entity(
        board_identifier=PARENT_BOARD_IDENTIFIER, owning_user_identifier=OWNING_USER_IDENTIFIER
    )


class TestCreateTaskInColumn:
    """Behavior of TaskManagementService.create_task_in_column."""

    async def test_appends_a_task_at_the_default_gap_when_the_column_is_empty(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        _stub_owned_column(fake_column_repository, fake_board_repository)
        fake_task_repository.find_highest_task_position_value_in_column.return_value = None
        fake_task_repository.create_task_record.side_effect = lambda task_entity: task_entity

        created_task_entity = await task_management_service.create_task_in_column(
            parent_column_identifier=PARENT_COLUMN_IDENTIFIER,
            requesting_user_identifier=OWNING_USER_IDENTIFIER,
            task_title="First task",
            task_description=None,
        )

        assert created_task_entity.task_position_value == DEFAULT_POSITION_GAP
        assert created_task_entity.parent_board_identifier == PARENT_BOARD_IDENTIFIER

    async def test_appends_a_task_after_the_highest_existing_position(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        _stub_owned_column(fake_column_repository, fake_board_repository)
        fake_task_repository.find_highest_task_position_value_in_column.return_value = 1000.0
        fake_task_repository.create_task_record.side_effect = lambda task_entity: task_entity

        created_task_entity = await task_management_service.create_task_in_column(
            parent_column_identifier=PARENT_COLUMN_IDENTIFIER,
            requesting_user_identifier=OWNING_USER_IDENTIFIER,
            task_title="Second task",
            task_description=None,
        )

        assert created_task_entity.task_position_value == 1000.0 + DEFAULT_POSITION_GAP

    async def test_raises_column_not_found_error_for_an_unknown_column(
        self,
        task_management_service: TaskManagementService,
        fake_column_repository: AsyncMock,
    ) -> None:
        fake_column_repository.find_column_by_identifier.return_value = None

        with pytest.raises(ColumnNotFoundError):
            await task_management_service.create_task_in_column(
                parent_column_identifier="missing-column-id",
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
                task_title="Task",
                task_description=None,
            )

    async def test_raises_unauthorized_board_access_error_for_a_non_owning_user(
        self,
        task_management_service: TaskManagementService,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        _stub_owned_column(fake_column_repository, fake_board_repository)

        with pytest.raises(UnauthorizedBoardAccessError):
            await task_management_service.create_task_in_column(
                parent_column_identifier=PARENT_COLUMN_IDENTIFIER,
                requesting_user_identifier=OTHER_USER_IDENTIFIER,
                task_title="Task",
                task_description=None,
            )


class TestFindAndUpdateAndDeleteTask:
    """Behavior of find/update/delete on TaskManagementService, scoped through board ownership."""

    async def test_find_task_owned_by_authenticated_user_returns_the_task(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        owned_task_entity = build_kanban_task_entity(
            parent_board_identifier=PARENT_BOARD_IDENTIFIER
        )
        fake_task_repository.find_task_by_identifier.return_value = owned_task_entity
        fake_board_repository.find_board_by_identifier.return_value = build_project_board_entity(
            board_identifier=PARENT_BOARD_IDENTIFIER, owning_user_identifier=OWNING_USER_IDENTIFIER
        )

        found_task_entity = await task_management_service.find_task_owned_by_authenticated_user(
            task_identifier=owned_task_entity.task_identifier,
            requesting_user_identifier=OWNING_USER_IDENTIFIER,
        )

        assert found_task_entity is owned_task_entity

    async def test_find_task_owned_by_authenticated_user_raises_task_not_found_error(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
    ) -> None:
        fake_task_repository.find_task_by_identifier.return_value = None

        with pytest.raises(TaskNotFoundError):
            await task_management_service.find_task_owned_by_authenticated_user(
                task_identifier="missing-task-id",
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
            )

    async def test_update_task_owned_by_authenticated_user_updates_title_and_description(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        owned_task_entity = build_kanban_task_entity(
            parent_board_identifier=PARENT_BOARD_IDENTIFIER
        )
        fake_task_repository.find_task_by_identifier.return_value = owned_task_entity
        fake_board_repository.find_board_by_identifier.return_value = build_project_board_entity(
            board_identifier=PARENT_BOARD_IDENTIFIER, owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        fake_task_repository.update_task_record.side_effect = lambda task_entity: task_entity

        updated_task_entity = await task_management_service.update_task_owned_by_authenticated_user(
            task_identifier=owned_task_entity.task_identifier,
            requesting_user_identifier=OWNING_USER_IDENTIFIER,
            task_title="Updated title",
            task_description="Updated description",
        )

        assert updated_task_entity.task_title == "Updated title"
        assert updated_task_entity.task_description == "Updated description"

    async def test_delete_task_owned_by_authenticated_user_deletes_the_task(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        owned_task_entity = build_kanban_task_entity(
            parent_board_identifier=PARENT_BOARD_IDENTIFIER
        )
        fake_task_repository.find_task_by_identifier.return_value = owned_task_entity
        fake_board_repository.find_board_by_identifier.return_value = build_project_board_entity(
            board_identifier=PARENT_BOARD_IDENTIFIER, owning_user_identifier=OWNING_USER_IDENTIFIER
        )

        await task_management_service.delete_task_owned_by_authenticated_user(
            task_identifier=owned_task_entity.task_identifier,
            requesting_user_identifier=OWNING_USER_IDENTIFIER,
        )

        fake_task_repository.delete_task_by_identifier.assert_awaited_once_with(
            owned_task_entity.task_identifier
        )

    async def test_raises_unauthorized_board_access_error_for_a_non_owning_user(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        someone_elses_task_entity = build_kanban_task_entity(
            parent_board_identifier=PARENT_BOARD_IDENTIFIER
        )
        fake_task_repository.find_task_by_identifier.return_value = someone_elses_task_entity
        fake_board_repository.find_board_by_identifier.return_value = build_project_board_entity(
            board_identifier=PARENT_BOARD_IDENTIFIER, owning_user_identifier=OWNING_USER_IDENTIFIER
        )

        with pytest.raises(UnauthorizedBoardAccessError):
            await task_management_service.delete_task_owned_by_authenticated_user(
                task_identifier=someone_elses_task_entity.task_identifier,
                requesting_user_identifier=OTHER_USER_IDENTIFIER,
            )

        fake_task_repository.delete_task_by_identifier.assert_not_awaited()
