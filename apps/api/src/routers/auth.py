"""Auth endpoints — Clerk webhooks and JWT utilities."""

from fastapi import APIRouter, Request, HTTPException, status
from shared.logging import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/webhook/clerk")
async def clerk_webhook(request: Request) -> dict:
    """Handle Clerk webhooks for user lifecycle events.

    Events: user.created, user.updated, user.deleted
    """
    payload = await request.json()
    event_type = payload.get("type", "unknown")

    logger.info("Clerk webhook received", event_type=event_type)

    # TODO: Verify webhook signature with CLERK_WEBHOOK_SECRET
    # TODO: Handle user.created, user.updated, user.deleted

    return {"status": "received", "event_type": event_type}
