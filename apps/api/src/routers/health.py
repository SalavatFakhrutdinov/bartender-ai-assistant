"""Health check endpoint."""

import time

from fastapi import APIRouter, Request

from shared.health import health_endpoint
from shared.logging import get_logger

router = APIRouter(tags=["health"])
logger = get_logger(__name__)

_START_TIME = time.time()


@router.get("/health")
async def health(request: Request) -> dict:
    """Service health check with dependency status."""
    checks = {}

    # Check Redis
    try:
        redis = request.app.state.redis
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
        logger.warning("Redis health check failed", error=str(e))

    # Check NATS (optional)
    try:
        nats = request.app.state.nats
        if nats.is_connected:
            checks["nats"] = "ok"
        else:
            checks["nats"] = "disconnected"
    except Exception as e:
        checks["nats"] = f"error: {e}"

    uptime = time.time() - _START_TIME
    result = await health_endpoint(
        checks=checks,
        version="0.1.0",
        uptime_seconds=uptime,
    )
    return result.model_dump()
