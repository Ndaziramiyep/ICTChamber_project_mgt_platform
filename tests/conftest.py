"""Fixtures shared across the entire test suite."""

from __future__ import annotations

import pytest

from app.core.application_settings import ApplicationSettings


@pytest.fixture(scope="session")
def test_application_settings() -> ApplicationSettings:
    """Return the ApplicationSettings loaded from the .env.test file used by the test suite."""
    return ApplicationSettings(_env_file=".env.test")
