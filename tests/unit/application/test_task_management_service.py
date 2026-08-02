"""Unit tests for TaskManagementService, with repositories faked via pytest-mock."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from app.application.services.task_management_service import TaskManagementService
from app.domain.entities.kanban_task_entity import KanbanTaskEntity
from app.domain.exceptions.board_domain_exceptions import UnauthorizedBoardAccessError
from app.domain.exceptions.column_domain_exceptions import ColumnNotFoundError
from app.domain.exceptions.task_domain_exceptions import (
    InvalidReorderTargetError,
    TaskNotFoundError,
)
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


TARGET_COLUMN_IDENTIFIER = "column-ghi-789"


class TestRepositionTaskOwnedByAuthenticatedUser:
    """Behavior of TaskManagementService.reposition_task_owned_by_authenticated_user."""

    def _stub_moving_task_and_target_column(
        self,
        fake_task_repository: AsyncMock,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
        moving_task_entity: KanbanTaskEntity,
        target_column_identifier: str,
        sibling_task_entities: list[KanbanTaskEntity],
    ) -> None:
        fake_task_repository.find_task_by_identifier.return_value = moving_task_entity
        fake_column_repository.find_column_by_identifier.return_value = build_board_column_entity(
            column_identifier=target_column_identifier,
            parent_board_identifier=PARENT_BOARD_IDENTIFIER,
        )
        fake_board_repository.find_board_by_identifier.return_value = build_project_board_entity(
            board_identifier=PARENT_BOARD_IDENTIFIER, owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        fake_task_repository.find_tasks_by_parent_column_identifier.return_value = (
            sibling_task_entities
        )
        fake_task_repository.update_task_record.side_effect = lambda task_entity: task_entity

    async def test_moves_task_to_the_top_when_previous_is_none(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        moving_task = build_kanban_task_entity(
            task_identifier="moving-task",
            parent_column_identifier=PARENT_COLUMN_IDENTIFIER,
            parent_board_identifier=PARENT_BOARD_IDENTIFIER,
            task_position_value=5000.0,
        )
        sibling_a = build_kanban_task_entity(
            task_identifier="sibling-a", task_position_value=1000.0
        )
        sibling_b = build_kanban_task_entity(
            task_identifier="sibling-b", task_position_value=2000.0
        )
        self._stub_moving_task_and_target_column(
            fake_task_repository,
            fake_column_repository,
            fake_board_repository,
            moving_task,
            PARENT_COLUMN_IDENTIFIER,
            [sibling_a, sibling_b],
        )

        repositioned_task = (
            await task_management_service.reposition_task_owned_by_authenticated_user(
                task_identifier=moving_task.task_identifier,
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
                target_column_identifier=PARENT_COLUMN_IDENTIFIER,
                previous_task_identifier=None,
                next_task_identifier="sibling-a",
            )
        )

        assert repositioned_task.task_position_value == 1000.0 - DEFAULT_POSITION_GAP

    async def test_moves_task_to_the_bottom_when_next_is_none(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        moving_task = build_kanban_task_entity(
            task_identifier="moving-task", task_position_value=5000.0
        )
        sibling_a = build_kanban_task_entity(
            task_identifier="sibling-a", task_position_value=1000.0
        )
        sibling_b = build_kanban_task_entity(
            task_identifier="sibling-b", task_position_value=2000.0
        )
        self._stub_moving_task_and_target_column(
            fake_task_repository,
            fake_column_repository,
            fake_board_repository,
            moving_task,
            PARENT_COLUMN_IDENTIFIER,
            [sibling_a, sibling_b],
        )

        repositioned_task = (
            await task_management_service.reposition_task_owned_by_authenticated_user(
                task_identifier=moving_task.task_identifier,
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
                target_column_identifier=PARENT_COLUMN_IDENTIFIER,
                previous_task_identifier="sibling-b",
                next_task_identifier=None,
            )
        )

        assert repositioned_task.task_position_value == 2000.0 + DEFAULT_POSITION_GAP

    async def test_moves_task_between_two_siblings_to_the_midpoint(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        moving_task = build_kanban_task_entity(
            task_identifier="moving-task", task_position_value=5000.0
        )
        sibling_a = build_kanban_task_entity(
            task_identifier="sibling-a", task_position_value=1000.0
        )
        sibling_b = build_kanban_task_entity(
            task_identifier="sibling-b", task_position_value=2000.0
        )
        self._stub_moving_task_and_target_column(
            fake_task_repository,
            fake_column_repository,
            fake_board_repository,
            moving_task,
            PARENT_COLUMN_IDENTIFIER,
            [sibling_a, sibling_b],
        )

        repositioned_task = (
            await task_management_service.reposition_task_owned_by_authenticated_user(
                task_identifier=moving_task.task_identifier,
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
                target_column_identifier=PARENT_COLUMN_IDENTIFIER,
                previous_task_identifier="sibling-a",
                next_task_identifier="sibling-b",
            )
        )

        assert repositioned_task.task_position_value == 1500.0

    async def test_moves_task_to_a_different_column_updates_parent_identifiers(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        moving_task = build_kanban_task_entity(
            task_identifier="moving-task",
            parent_column_identifier=PARENT_COLUMN_IDENTIFIER,
            parent_board_identifier=PARENT_BOARD_IDENTIFIER,
            task_position_value=5000.0,
        )
        self._stub_moving_task_and_target_column(
            fake_task_repository,
            fake_column_repository,
            fake_board_repository,
            moving_task,
            TARGET_COLUMN_IDENTIFIER,
            [],
        )

        repositioned_task = (
            await task_management_service.reposition_task_owned_by_authenticated_user(
                task_identifier=moving_task.task_identifier,
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
                target_column_identifier=TARGET_COLUMN_IDENTIFIER,
                previous_task_identifier=None,
                next_task_identifier=None,
            )
        )

        assert repositioned_task.parent_column_identifier == TARGET_COLUMN_IDENTIFIER
        assert repositioned_task.parent_board_identifier == PARENT_BOARD_IDENTIFIER
        assert repositioned_task.task_position_value == DEFAULT_POSITION_GAP
        fake_task_repository.update_task_record.assert_awaited_once_with(moving_task)

    async def test_rebalances_every_sibling_when_the_gap_is_too_small(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        moving_task = build_kanban_task_entity(
            task_identifier="moving-task", task_position_value=5000.0
        )
        sibling_a = build_kanban_task_entity(
            task_identifier="sibling-a", task_position_value=1000.0
        )
        sibling_b = build_kanban_task_entity(
            task_identifier="sibling-b", task_position_value=1000.0000001
        )
        self._stub_moving_task_and_target_column(
            fake_task_repository,
            fake_column_repository,
            fake_board_repository,
            moving_task,
            PARENT_COLUMN_IDENTIFIER,
            [sibling_a, sibling_b],
        )

        await task_management_service.reposition_task_owned_by_authenticated_user(
            task_identifier=moving_task.task_identifier,
            requesting_user_identifier=OWNING_USER_IDENTIFIER,
            target_column_identifier=PARENT_COLUMN_IDENTIFIER,
            previous_task_identifier="sibling-a",
            next_task_identifier="sibling-b",
        )

        assert sibling_a.task_position_value == DEFAULT_POSITION_GAP
        assert moving_task.task_position_value == DEFAULT_POSITION_GAP * 2
        assert sibling_b.task_position_value == DEFAULT_POSITION_GAP * 3
        assert fake_task_repository.update_task_record.await_count == 3

    async def test_raises_invalid_reorder_target_error_when_previous_task_is_not_in_target_column(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        moving_task = build_kanban_task_entity(task_identifier="moving-task")
        self._stub_moving_task_and_target_column(
            fake_task_repository,
            fake_column_repository,
            fake_board_repository,
            moving_task,
            PARENT_COLUMN_IDENTIFIER,
            [],
        )

        with pytest.raises(InvalidReorderTargetError):
            await task_management_service.reposition_task_owned_by_authenticated_user(
                task_identifier=moving_task.task_identifier,
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
                target_column_identifier=PARENT_COLUMN_IDENTIFIER,
                previous_task_identifier="not-a-sibling",
                next_task_identifier=None,
            )

    async def test_raises_invalid_reorder_target_error_when_neighbors_are_not_adjacent(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        moving_task = build_kanban_task_entity(task_identifier="moving-task")
        sibling_a = build_kanban_task_entity(
            task_identifier="sibling-a", task_position_value=1000.0
        )
        sibling_b = build_kanban_task_entity(
            task_identifier="sibling-b", task_position_value=2000.0
        )
        sibling_c = build_kanban_task_entity(
            task_identifier="sibling-c", task_position_value=3000.0
        )
        self._stub_moving_task_and_target_column(
            fake_task_repository,
            fake_column_repository,
            fake_board_repository,
            moving_task,
            PARENT_COLUMN_IDENTIFIER,
            [sibling_a, sibling_b, sibling_c],
        )

        with pytest.raises(InvalidReorderTargetError):
            await task_management_service.reposition_task_owned_by_authenticated_user(
                task_identifier=moving_task.task_identifier,
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
                target_column_identifier=PARENT_COLUMN_IDENTIFIER,
                previous_task_identifier="sibling-a",
                next_task_identifier="sibling-c",
            )

    async def test_raises_task_not_found_error_for_an_unknown_task(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
    ) -> None:
        fake_task_repository.find_task_by_identifier.return_value = None

        with pytest.raises(TaskNotFoundError):
            await task_management_service.reposition_task_owned_by_authenticated_user(
                task_identifier="missing-task-id",
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
                target_column_identifier=PARENT_COLUMN_IDENTIFIER,
                previous_task_identifier=None,
                next_task_identifier=None,
            )

    async def test_raises_column_not_found_error_for_an_unknown_target_column(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        moving_task = build_kanban_task_entity(
            task_identifier="moving-task", parent_board_identifier=PARENT_BOARD_IDENTIFIER
        )
        fake_task_repository.find_task_by_identifier.return_value = moving_task
        fake_board_repository.find_board_by_identifier.return_value = build_project_board_entity(
            board_identifier=PARENT_BOARD_IDENTIFIER, owning_user_identifier=OWNING_USER_IDENTIFIER
        )
        fake_column_repository.find_column_by_identifier.return_value = None

        with pytest.raises(ColumnNotFoundError):
            await task_management_service.reposition_task_owned_by_authenticated_user(
                task_identifier=moving_task.task_identifier,
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
                target_column_identifier="missing-column-id",
                previous_task_identifier=None,
                next_task_identifier=None,
            )

    async def test_raises_unauthorized_board_access_error_when_target_columns_board_is_not_owned(
        self,
        task_management_service: TaskManagementService,
        fake_task_repository: AsyncMock,
        fake_column_repository: AsyncMock,
        fake_board_repository: AsyncMock,
    ) -> None:
        moving_task = build_kanban_task_entity(
            task_identifier="moving-task", parent_board_identifier=PARENT_BOARD_IDENTIFIER
        )
        fake_task_repository.find_task_by_identifier.return_value = moving_task
        fake_column_repository.find_column_by_identifier.return_value = build_board_column_entity(
            column_identifier=TARGET_COLUMN_IDENTIFIER,
            parent_board_identifier="someone-elses-board",
        )
        fake_board_repository.find_board_by_identifier.side_effect = [
            build_project_board_entity(
                board_identifier=PARENT_BOARD_IDENTIFIER,
                owning_user_identifier=OWNING_USER_IDENTIFIER,
            ),
            build_project_board_entity(
                board_identifier="someone-elses-board",
                owning_user_identifier=OTHER_USER_IDENTIFIER,
            ),
        ]

        with pytest.raises(UnauthorizedBoardAccessError):
            await task_management_service.reposition_task_owned_by_authenticated_user(
                task_identifier=moving_task.task_identifier,
                requesting_user_identifier=OWNING_USER_IDENTIFIER,
                target_column_identifier=TARGET_COLUMN_IDENTIFIER,
                previous_task_identifier=None,
                next_task_identifier=None,
            )
