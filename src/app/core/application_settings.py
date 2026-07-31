"""Strongly-typed application configuration loaded from environment variables or a .env file."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationSettings(BaseSettings):
    """Application configuration values required to run the API and connect to MongoDB."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    application_environment_name: str = "development"

    mongodb_connection_uri: str
    mongodb_database_name: str

    jwt_secret_key: str
    jwt_access_token_expiry_minutes: int = 15
    jwt_refresh_token_expiry_days: int = 7

    allowed_cors_origins: str = ""

    @property
    def allowed_cors_origin_list(self) -> list[str]:
        """Return the comma-separated CORS origins setting split into a list of trimmed origins."""
        return [
            single_cors_origin.strip()
            for single_cors_origin in self.allowed_cors_origins.split(",")
            if single_cors_origin.strip()
        ]


@lru_cache(maxsize=1)
def get_cached_application_settings() -> ApplicationSettings:
    """Return a process-wide cached ApplicationSettings instance built from the default .env
    file."""
    return ApplicationSettings()
