"""Dependency injection for FastAPI."""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis
from shared.config import get_settings
from shared.models.user import User
from shared.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.src.core.config import get_api_settings

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    from shared.models.base import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis(request: Request) -> Redis:
    """Return the Redis connection from app state."""
    return request.app.state.redis


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Validate Clerk JWT and return user claims.

    In Phase 0, this is a simplified stub that validates the token format.
    Full JWKS validation is implemented in middleware/auth.py.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    # TODO: Full JWT validation via Clerk JWKS endpoint
    # For Phase 0, return a minimal user dict for development
    return {
        "sub": "stub-user-id",
        "email": "dev@example.com",
        "tier": "free",
    }


async def get_effective_tier(user: dict = Depends(get_current_user)) -> str:
    """Return the effective tier considering launch promotion."""
    # TODO: Query database for launch_promo_ends_at
    # For Phase 0, return tier from JWT claims
    return user.get("tier", "free")
