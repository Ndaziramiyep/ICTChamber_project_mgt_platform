"""Health check endpoint used by deployment tooling to confirm the API is responsive."""

from __future__ import annotations

from fastapi import APIRouter

health_router = APIRouter(tags=["health"])


@health_router.get("/health")
async def report_application_health_status() -> dict[str, str]:
    """Return a simple payload confirming the API process is up and responding."""
    return {"status": "healthy"}
