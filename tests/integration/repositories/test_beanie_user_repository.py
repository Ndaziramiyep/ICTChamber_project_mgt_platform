"""Integration tests for BeanieUserRepository against a real MongoDB test database."""

from __future__ import annotations

from app.infrastructure.persistence.repositories.beanie_user_repository import (
    BeanieUserRepository,
)
from tests.factories.user_factory import build_registered_user_entity


class TestCreateAndFindUserRecord:
    """Persistence round-trip behavior for user records."""

    async def test_create_user_record_populates_a_generated_identifier(self) -> None:
        beanie_user_repository = BeanieUserRepository()
        user_entity_to_persist = build_registered_user_entity(
            user_identifier="", email_address="round.trip@example.com"
        )

        persisted_user_entity = await beanie_user_repository.create_user_record(
            user_entity_to_persist
        )

        assert persisted_user_entity.user_identifier
        assert persisted_user_entity.email_address == "round.trip@example.com"

    async def test_find_user_by_email_address_returns_the_persisted_user(self) -> None:
        beanie_user_repository = BeanieUserRepository()
        await beanie_user_repository.create_user_record(
            build_registered_user_entity(user_identifier="", email_address="findable@example.com")
        )

        found_user_entity = await beanie_user_repository.find_user_by_email_address(
            "findable@example.com"
        )

        assert found_user_entity is not None
        assert found_user_entity.email_address == "findable@example.com"

    async def test_find_user_by_email_address_returns_none_for_an_unknown_address(self) -> None:
        beanie_user_repository = BeanieUserRepository()

        found_user_entity = await beanie_user_repository.find_user_by_email_address(
            "nobody@example.com"
        )

        assert found_user_entity is None

    async def test_find_user_by_identifier_returns_the_persisted_user(self) -> None:
        beanie_user_repository = BeanieUserRepository()
        persisted_user_entity = await beanie_user_repository.create_user_record(
            build_registered_user_entity(user_identifier="", email_address="by.id@example.com")
        )

        found_user_entity = await beanie_user_repository.find_user_by_identifier(
            persisted_user_entity.user_identifier
        )

        assert found_user_entity is not None
        assert found_user_entity.user_identifier == persisted_user_entity.user_identifier

    async def test_find_user_by_identifier_returns_none_for_an_invalid_identifier(self) -> None:
        beanie_user_repository = BeanieUserRepository()

        found_user_entity = await beanie_user_repository.find_user_by_identifier("not-an-object-id")

        assert found_user_entity is None
