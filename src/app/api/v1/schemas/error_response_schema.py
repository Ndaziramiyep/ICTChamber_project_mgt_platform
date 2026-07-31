"""Consistent error response contract returned for every 4xx/5xx HTTP response."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorResponseSchema(BaseModel):
    """The uniform JSON body returned whenever a request fails."""

    error_code: str
    error_message: str
    error_details: dict[str, Any] | None = None
