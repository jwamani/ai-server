"""Typed application settings loaded from the environment."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the API control plane."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_environment: Literal["development", "test", "production"] = Field(
        default="development",
        validation_alias="APP_ENV",
    )
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    jwt_secret: str | None = Field(default=None, min_length=32, validation_alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = Field(default=60, ge=1, le=1_440)
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")
    cors_origins: tuple[AnyHttpUrl, ...] = Field(
        default=(AnyHttpUrl("http://localhost:5173"),),
        validation_alias="API_CORS_ORIGINS",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide immutable settings instance."""

    return Settings()
