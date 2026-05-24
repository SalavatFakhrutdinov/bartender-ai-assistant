"""FastAPI application factory for Bartender AI Assistant API."""

from fastapi import FastAPI

from shared.logging import configure_logging, get_logger
from shared.config import get_settings
from shared.models.base import configure_async_session

from apps.api.src.core.config import get_api_settings
from apps.api.src.core.lifespan import lifespan
from apps.api.src.middleware.cors import add_cors_middleware
from apps.api.src.middleware.auth import ClerkAuthMiddleware
from apps.api.src.middleware.rate_limit import RateLimitMiddleware
from apps.api.src.routers import health, auth

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    api_settings = get_api_settings()

    configure_logging(log_level=settings.log_level, json_format=not settings.debug)
    configure_async_session(settings.database.async_url)

    app = FastAPI(
        title="Bartender AI Assistant API",
        description="Backend API for the Bartender AI Assistant",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware
    add_cors_middleware(app, origins=api_settings.cors_origins)
    app.add_middleware(ClerkAuthMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # Routers
    app.include_router(health.router)
    app.include_router(auth.router)

    @app.get("/")
    async def root() -> dict:
        return {
            "name": "Bartender AI Assistant API",
            "version": "0.1.0",
            "status": "operational",
        }

    logger.info("FastAPI app created")
    return app


app = create_app()
