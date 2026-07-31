"""FastAPI application factory: wires configuration, database lifecycle, routers, and error
handling."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router_registry import api_v1_router
from app.core.application_settings import ApplicationSettings, get_cached_application_settings
from app.core.database_connection_manager import DatabaseConnectionManager
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_configuration import configure_application_logging


def create_fastapi_application(application_settings: ApplicationSettings | None = None) -> FastAPI:
    """Build and fully configure a FastAPI application instance.

    Accepts an explicit ApplicationSettings so integration tests can build an application wired
    to a dedicated test database, instead of always reusing the process-wide cached settings.
    """
    application_settings = application_settings or get_cached_application_settings()
    configure_application_logging(application_settings.application_environment_name)
    database_connection_manager = DatabaseConnectionManager(application_settings)

    @asynccontextmanager
    async def manage_application_lifespan(_fastapi_application: FastAPI) -> AsyncIterator[None]:
        """Open the MongoDB connection on startup and close it on shutdown."""
        await database_connection_manager.connect_and_initialize_document_models()
        yield
        await database_connection_manager.close_mongo_client_connection()

    fastapi_application = FastAPI(
        title="ICT Chamber Kanban Platform API",
        version="0.1.0",
        lifespan=manage_application_lifespan,
    )

    fastapi_application.add_middleware(
        CORSMiddleware,
        allow_origins=application_settings.allowed_cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(fastapi_application)
    fastapi_application.include_router(api_v1_router)

    return fastapi_application


fastapi_application_instance = create_fastapi_application()
