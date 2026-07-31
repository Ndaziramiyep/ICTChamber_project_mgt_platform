"""Aggregates all version-1 API routers into a single router mounted by the application."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routers.authentication_router import authentication_router
from app.api.v1.routers.board_router import board_router
from app.api.v1.routers.column_router import column_router
from app.api.v1.routers.health_router import health_router
from app.api.v1.routers.task_router import task_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(authentication_router)
api_v1_router.include_router(board_router)
api_v1_router.include_router(column_router)
api_v1_router.include_router(task_router)
