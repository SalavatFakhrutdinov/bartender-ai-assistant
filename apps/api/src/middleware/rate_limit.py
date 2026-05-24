"""Redis-based rate limiting middleware."""

import time

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from shared.logging import get_logger
from shared.config import get_settings

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting based on user tier (free vs paid).

    Uses Redis sliding window counters.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health and docs
        if request.url.path in ("/health", "/docs", "/openapi.json"):
            return await call_next(request)

        # TODO: Full Redis-based rate limiting in Phase 1
        # For Phase 0, stubbed — always allow
        return await call_next(request)


async def check_rate_limit(redis, user_id: str, tier: str) -> dict:
    """Check if user is within rate limits.

    Returns rate limit info with remaining requests.
    """
    settings = get_settings()

    if tier == "paid":
        rpm_limit = settings.rate_limit.paid_rpm
        rpd_limit = settings.rate_limit.paid_rpd
    else:
        rpm_limit = settings.rate_limit.free_rpm
        rpd_limit = settings.rate_limit.free_rpd

    now = int(time.time())
    minute_key = f"rate_limit:{user_id}:minute"
    day_key = f"rate_limit:{user_id}:day"

    # Increment counters
    pipe = redis.pipeline()
    pipe.incr(minute_key)
    pipe.expire(minute_key, 60)
    pipe.incr(day_key)
    pipe.expire(day_key, 86400)
    results = await pipe.execute()

    minute_count = results[0]
    day_count = results[2]

    remaining = min(rpm_limit - minute_count, rpd_limit - day_count)

    if minute_count > rpm_limit or day_count > rpd_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )

    return {
        "tier": tier,
        "requests_remaining": max(0, remaining),
        "reset_at": now + 60,
    }
