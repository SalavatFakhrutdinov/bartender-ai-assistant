"""Pydantic-Settings based configuration for all services.

Environment variables are automatically loaded from `.env` files and
validated against these schema definitions.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """PostgreSQL configuration."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    host: str = "localhost"
    port: int = 5432
    db: str = "bartender_ai"
    user: str = "bartender"
    password: str = "changeme"

    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class RedisSettings(BaseSettings):
    """Redis configuration."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = "localhost"
    port: int = 6379
    url: str = "redis://localhost:6379/0"


class QdrantSettings(BaseSettings):
    """Qdrant vector database configuration."""

    model_config = SettingsConfigDict(env_prefix="QDRANT_")

    host: str = "localhost"
    port: int = 6333
    url: str = "http://localhost:6333"


class NatsSettings(BaseSettings):
    """NATS JetStream configuration."""

    model_config = SettingsConfigDict(env_prefix="NATS_")

    url: str = "nats://localhost:4222"


class ClerkSettings(BaseSettings):
    """Clerk authentication configuration."""

    model_config = SettingsConfigDict(env_prefix="CLERK_")

    publishable_key: str = ""
    secret_key: str = ""
    jwks_url: str = ""
    webhook_secret: str = ""


class LLMProviderSettings(BaseSettings):
    """LLM API keys and endpoints."""

    model_config = SettingsConfigDict(env_prefix="")

    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration."""

    model_config = SettingsConfigDict(env_prefix="RATE_LIMIT_")

    free_rpm: int = 10
    free_rpd: int = 100
    paid_rpm: int = 60
    paid_rpd: int = 1000


class AgentSettings(BaseSettings):
    """Agent swarm configuration."""

    model_config = SettingsConfigDict(env_prefix="AGENT_")

    heartbeat_interval_seconds: int = 30
    heartbeat_timeout_seconds: int = 90
    max_retries: int = 3


class Settings(BaseSettings):
    """Root settings composition."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field(default="development", alias="ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Sub-settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    qdrant: QdrantSettings = QdrantSettings()
    nats: NatsSettings = NatsSettings()
    clerk: ClerkSettings = ClerkSettings()
    llm: LLMProviderSettings = LLMProviderSettings()
    rate_limit: RateLimitSettings = RateLimitSettings()
    agent: AgentSettings = AgentSettings()


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance.

    Using lru_cache ensures settings are loaded once per process and
    shared across all callers.
    """
    return Settings()
