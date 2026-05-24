"""Health check utilities for FastAPI services."""

from shared.health.check import HealthCheck, health_endpoint

__all__ = ["HealthCheck", "health_endpoint"]
