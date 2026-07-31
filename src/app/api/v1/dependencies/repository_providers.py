"""FastAPI dependency providers supplying concrete repository implementations.

Each provider returns the abstract interface type so that services depending on it via
FastAPI's Depends() remain coupled only to the domain contract, never to Beanie directly.
"""

from __future__ import annotations

from app.domain.repositories.board_repository_interface import BoardRepositoryInterface
from app.domain.repositories.column_repository_interface import ColumnRepositoryInterface
from app.domain.repositories.task_repository_interface import TaskRepositoryInterface
from app.domain.repositories.user_repository_interface import UserRepositoryInterface
from app.infrastructure.persistence.repositories.beanie_board_repository import (
    BeanieBoardRepository,
)
from app.infrastructure.persistence.repositories.beanie_column_repository import (
    BeanieColumnRepository,
)
from app.infrastructure.persistence.repositories.beanie_task_repository import (
    BeanieTaskRepository,
)
from app.infrastructure.persistence.repositories.beanie_user_repository import (
    BeanieUserRepository,
)


def provide_user_repository() -> UserRepositoryInterface:
    """Supply the concrete Beanie-backed user repository for dependency injection."""
    return BeanieUserRepository()


def provide_board_repository() -> BoardRepositoryInterface:
    """Supply the concrete Beanie-backed board repository for dependency injection."""
    return BeanieBoardRepository()


def provide_column_repository() -> ColumnRepositoryInterface:
    """Supply the concrete Beanie-backed column repository for dependency injection."""
    return BeanieColumnRepository()


def provide_task_repository() -> TaskRepositoryInterface:
    """Supply the concrete Beanie-backed task repository for dependency injection."""
    return BeanieTaskRepository()
