"""Health check endpoint for FastAPI services.

Provides a standardized health response format used by all services
and consumed by the Health Monitor.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class HealthCheck(BaseModel):
    """Health check response model."""

    status: str = Field(default="ok", pattern="^(ok|degraded|unhealthy)$")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "0.1.0"
    checks: dict[str, Any] = Field(default_factory=dict)
    uptime_seconds: float = 0.0


async def health_endpoint(
    checks: dict[str, Any] | None = None,
    version: str = "0.1.0",
    uptime_seconds: float = 0.0,
) -> HealthCheck:
    """Generate a health check response.

    Args:
        checks: Dict of dependency checks, e.g.:
            {"database": "ok", "redis": "ok", "nats": "degraded"}
        version: Service version string
        uptime_seconds: Process uptime

    Returns:
        HealthCheck response with overall status derived from checks
    """
    all_checks = checks or {}
    any_degraded = any(
        v != "ok" and v != "connected" and v is not True
        for v in all_checks.values()
    )
    any_unhealthy = any(
        v in ("failed", "unhealthy", "error", False)
        for v in all_checks.values()
    )

    status = "ok"
    if any_degraded:
        status = "degraded"
    if any_unhealthy:
        status = "unhealthy"

    return HealthCheck(
        status=status,
        version=version,
        checks=all_checks,
        uptime_seconds=uptime_seconds,
    )
