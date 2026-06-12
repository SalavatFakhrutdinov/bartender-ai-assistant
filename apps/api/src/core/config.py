"""API service-specific configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import SettingsConfigDict
from shared.config import Settings as SharedSettings


class ApiSettings(SharedSettings):
    """API service settings extending shared configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: list[str] = Field(default=["http://localhost:3000"], alias="CORS_ORIGINS")


@lru_cache
def get_api_settings() -> ApiSettings:
    return ApiSettings()
