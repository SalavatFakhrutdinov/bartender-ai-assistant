"""Clerk JWT validation middleware.

In Phase 0, this is a simplified implementation. Full JWKS endpoint
caching and signature verification will be added in Phase 1.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from shared.logging import get_logger

logger = get_logger(__name__)


class ClerkAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates Clerk JWT on protected routes."""

    async def dispatch(self, request: Request, call_next):
        # Skip auth for health and public endpoints
        if request.url.path in ("/health", "/", "/docs", "/openapi.json"):
            return await call_next(request)

        # TODO: Full JWT validation in Phase 1
        # For Phase 0, pass through with stub user for development
        request.state.user = {
            "sub": "stub-user-id",
            "email": "dev@example.com",
            "tier": "free",
        }

        return await call_next(request)
