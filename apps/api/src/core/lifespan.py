"""FastAPI lifespan — startup/shutdown hooks for external services."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis
from shared.config import get_settings
from shared.logging import configure_logging, get_logger
from shared.nats_client import NatsClient

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle: connect to DB, Redis, NATS, Qdrant on startup."""
    settings = get_settings()
    configure_logging(log_level=settings.log_level, json_format=not settings.debug)

    logger.info("Starting up API service", version="0.1.0")

    # Redis connection
    app.state.redis = Redis.from_url(settings.redis.url, decode_responses=True)
    try:
        await app.state.redis.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.error("Redis connection failed", error=str(e))

    # NATS connection (optional in Phase 0, stubbed)
    app.state.nats = NatsClient(nats_url=settings.nats.url)
    try:
        await app.state.nats.connect()
        await app.state.nats.initialize_streams()
        logger.info("Connected to NATS")
    except Exception as e:
        logger.warning("NATS connection failed (non-critical for Phase 0)", error=str(e))

    yield

    # Shutdown
    logger.info("Shutting down API service")
    if hasattr(app.state, "redis"):
        await app.state.redis.close()
    if hasattr(app.state, "nats"):
        await app.state.nats.disconnect()
