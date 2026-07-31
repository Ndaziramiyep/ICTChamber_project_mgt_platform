"""Owns the lifecycle of the MongoDB client connection and Beanie document initialization."""

from __future__ import annotations

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.core.application_settings import ApplicationSettings
from app.infrastructure.persistence.documents.board_document import ProjectBoardDocument
from app.infrastructure.persistence.documents.column_document import BoardColumnDocument
from app.infrastructure.persistence.documents.task_document import KanbanTaskDocument
from app.infrastructure.persistence.documents.user_document import RegisteredUserDocument

ALL_DOCUMENT_MODELS = [
    RegisteredUserDocument,
    ProjectBoardDocument,
    BoardColumnDocument,
    KanbanTaskDocument,
]


class DatabaseConnectionManager:
    """Opens and closes the MongoDB client connection used by the application."""

    def __init__(self, application_settings: ApplicationSettings) -> None:
        """Store the application settings needed to build the MongoDB client connection."""
        self._application_settings = application_settings
        self._mongo_client: AsyncMongoClient | None = None

    async def connect_and_initialize_document_models(self) -> None:
        """Open the MongoDB connection and register all Beanie document models against it."""
        self._mongo_client = AsyncMongoClient(self._application_settings.mongodb_connection_uri)
        await init_beanie(
            database=self._mongo_client[self._application_settings.mongodb_database_name],
            document_models=ALL_DOCUMENT_MODELS,
        )

    async def close_mongo_client_connection(self) -> None:
        """Close the underlying MongoDB client connection if one was previously opened."""
        if self._mongo_client is not None:
            await self._mongo_client.close()
            self._mongo_client = None
