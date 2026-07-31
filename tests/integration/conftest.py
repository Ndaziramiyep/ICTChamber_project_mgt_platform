"""Fixtures connecting the integration test suite to a real MongoDB test database.

No mocks or fakes are used here by design: these tests exercise the real Beanie repository
implementations and the real FastAPI application against an actual MongoDB instance, using a
dedicated database that is dropped after the session and cleaned between individual tests.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.core.application_settings import ApplicationSettings
from app.core.database_connection_manager import ALL_DOCUMENT_MODELS


@pytest.fixture(scope="session")
async def real_test_mongo_client(
    test_application_settings: ApplicationSettings,
) -> AsyncIterator[AsyncMongoClient]:
    """Connect Beanie to the real MongoDB test database for the duration of the test session."""
    mongo_client: AsyncMongoClient = AsyncMongoClient(
        test_application_settings.mongodb_connection_uri
    )
    await init_beanie(
        database=mongo_client[test_application_settings.mongodb_database_name],
        document_models=ALL_DOCUMENT_MODELS,
    )

    yield mongo_client

    await mongo_client.drop_database(test_application_settings.mongodb_database_name)
    await mongo_client.close()


@pytest.fixture(autouse=True)
async def clean_database_between_tests(
    real_test_mongo_client: AsyncMongoClient,
    test_application_settings: ApplicationSettings,
) -> AsyncIterator[None]:
    """Delete every document from every collection after each integration test runs.

    Documents are deleted rather than the collections being dropped so that the indexes
    Beanie created once at session start-up (e.g. the unique index on email_address) remain
    in place for every test, instead of only existing for the first test in the session.
    """
    yield

    test_database = real_test_mongo_client[test_application_settings.mongodb_database_name]
    for existing_collection_name in await test_database.list_collection_names():
        await test_database[existing_collection_name].delete_many({})
