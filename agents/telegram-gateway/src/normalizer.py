"""Telegram message → NATS event normalization."""

from uuid import uuid4

from telegram import Update

from shared.events.schemas import HumanMessage, HumanCommand, EventMeta
from shared.logging import get_logger

logger = get_logger(__name__)


class Normalizer:
    """Converts Telegram updates to typed NATS events."""

    def telegram_to_event(self, update: Update) -> HumanMessage | HumanCommand:
        """Convert a Telegram update to a NATS event."""
        message = update.effective_message
        if not message or not message.text:
            raise ValueError("No text in message")

        user = message.from_user
        chat = message.chat

        meta = EventMeta(
            event_id=str(uuid4()),
            correlation_id=str(uuid4()),
            source="telegram_gateway",
        )

        text = message.text.strip()

        # Check if it's a command
        if text.startswith("/"):
            parts = text.split(maxsplit=1)
            command = parts[0][1:]  # Remove leading /
            args = parts[1] if len(parts) > 1 else ""

            return HumanCommand(
                meta=meta,
                user_id=str(user.id) if user else "unknown",
                username=user.username if user else None,
                command=command,
                args=args,
                chat_id=str(chat.id),
                thread_id=str(message.message_thread_id) if message.message_thread_id else None,
            )

        # Regular message
        return HumanMessage(
            meta=meta,
            user_id=str(user.id) if user else "unknown",
            username=user.username if user else None,
            message_text=text,
            chat_id=str(chat.id),
            thread_id=str(message.message_thread_id) if message.message_thread_id else None,
        )
