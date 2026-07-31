"""Translates domain exceptions and validation errors into the uniform HTTP error contract."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.schemas.error_response_schema import ErrorResponseSchema
from app.domain.exceptions import (
    AuthenticationError,
    DomainError,
    ResourceConflictError,
    ResourceNotFoundError,
    UnauthorizedAccessError,
)

_application_logger = logging.getLogger("app")


def _build_error_json_response(
    status_code: int, error_code: str, error_message: str
) -> JSONResponse:
    """Serialize an ErrorResponseSchema into a JSONResponse with the given HTTP status code."""
    error_response_body = ErrorResponseSchema(error_code=error_code, error_message=error_message)
    return JSONResponse(status_code=status_code, content=error_response_body.model_dump())


async def handle_resource_not_found_error(
    _request: Request, raised_exception: ResourceNotFoundError
) -> JSONResponse:
    """Translate any ResourceNotFoundError subclass into a 404 response."""
    return _build_error_json_response(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code=type(raised_exception).__name__,
        error_message=str(raised_exception),
    )


async def handle_unauthorized_access_error(
    _request: Request, raised_exception: UnauthorizedAccessError
) -> JSONResponse:
    """Translate any UnauthorizedAccessError subclass into a 403 response."""
    return _build_error_json_response(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code=type(raised_exception).__name__,
        error_message=str(raised_exception),
    )


async def handle_resource_conflict_error(
    _request: Request, raised_exception: ResourceConflictError
) -> JSONResponse:
    """Translate any ResourceConflictError subclass into a 409 response."""
    return _build_error_json_response(
        status_code=status.HTTP_409_CONFLICT,
        error_code=type(raised_exception).__name__,
        error_message=str(raised_exception),
    )


async def handle_authentication_error(
    _request: Request, raised_exception: AuthenticationError
) -> JSONResponse:
    """Translate any AuthenticationError subclass into a 401 response."""
    return _build_error_json_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code=type(raised_exception).__name__,
        error_message=str(raised_exception),
    )


async def handle_request_validation_error(
    _request: Request, raised_exception: RequestValidationError
) -> JSONResponse:
    """Translate FastAPI/Pydantic request validation errors into the uniform error contract."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=ErrorResponseSchema(
            error_code="REQUEST_VALIDATION_ERROR",
            error_message="The request payload failed validation.",
            error_details={"validation_errors": raised_exception.errors()},
        ).model_dump(),
    )


async def handle_unexpected_domain_error(
    _request: Request, raised_exception: DomainError
) -> JSONResponse:
    """Catch-all for DomainError subclasses without a more specific registered handler."""
    _application_logger.exception("Unhandled domain error", exc_info=raised_exception)
    return _build_error_json_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code=type(raised_exception).__name__,
        error_message=str(raised_exception),
    )


async def handle_unexpected_server_error(
    _request: Request, raised_exception: Exception
) -> JSONResponse:
    """Catch-all for any exception not otherwise handled, logged with a generic public message."""
    _application_logger.exception("Unhandled server error", exc_info=raised_exception)
    return _build_error_json_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
        error_message="An unexpected error occurred while processing the request.",
    )


def register_exception_handlers(fastapi_application: FastAPI) -> None:
    """Register every domain-exception-to-HTTP-response translation on the given application."""
    # Starlette's add_exception_handler() stub is contravariant on the exception parameter, so
    # handlers typed to a specific DomainError subclass (rather than the bare Exception base) are
    # flagged by mypy even though Starlette dispatches by exact/registered exception type at
    # runtime; this is a known false positive, hence the targeted ignores below.
    fastapi_application.add_exception_handler(
        ResourceNotFoundError, handle_resource_not_found_error  # type: ignore[arg-type]
    )
    fastapi_application.add_exception_handler(
        UnauthorizedAccessError, handle_unauthorized_access_error  # type: ignore[arg-type]
    )
    fastapi_application.add_exception_handler(
        ResourceConflictError, handle_resource_conflict_error  # type: ignore[arg-type]
    )
    fastapi_application.add_exception_handler(
        AuthenticationError, handle_authentication_error  # type: ignore[arg-type]
    )
    fastapi_application.add_exception_handler(
        RequestValidationError, handle_request_validation_error  # type: ignore[arg-type]
    )
    fastapi_application.add_exception_handler(
        DomainError, handle_unexpected_domain_error  # type: ignore[arg-type]
    )
    fastapi_application.add_exception_handler(Exception, handle_unexpected_server_error)
