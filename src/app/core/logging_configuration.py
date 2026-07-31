"""Structured logging setup for the application."""

from __future__ import annotations

import logging
import sys


def configure_application_logging(application_environment_name: str) -> None:
    """Configure the root logger with a consistent format for the given environment."""
    logging_level = logging.DEBUG if application_environment_name == "development" else logging.INFO

    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
        force=True,
    )
    logging.getLogger("pymongo").setLevel(logging.WARNING)
