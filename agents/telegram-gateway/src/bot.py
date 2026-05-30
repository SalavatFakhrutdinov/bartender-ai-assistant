"""Telegram Bot implementation."""

import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from shared.logging import get_logger
from shared.nats_client import NatsClient
from shared.config import get_settings
from src.normalizer import Normalizer
from src.surfacer import Surfacer

logger = get_logger(__name__)


class TelegramBot:
    """Telegram bot that bridges human messages to the NATS event bus."""

    def __init__(self):
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        self.normalizer = Normalizer()
        self.surfacer = Surfacer()
        self.nats: NatsClient | None = None
        self.app: Application | None = None

    async def setup(self) -> None:
        """Initialize bot and NATS connection."""
        settings = get_settings()

        self.nats = NatsClient(nats_url=settings.nats.url)
        await self.nats.connect()

        self.app = Application.builder().token(self.token).build()

        # Register handlers
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("analyze", self._cmd_analyze))
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message))

        logger.info("Telegram bot initialized")

    async def run(self) -> None:
        """Start the bot (blocking)."""
        if not self.app:
            raise RuntimeError("Bot not set up. Call setup() first.")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        logger.info("Telegram bot polling started")

    async def stop(self) -> None:
        """Stop the bot gracefully."""
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
        if self.nats:
            await self.nats.disconnect()

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        await update.message.reply_text(
            "🍸 *Bartender AI Assistant — Agent Swarm*\n\n"
            "Available commands:\n"
            "• /analyze <feature> — Create a development ticket\n"
            "• /status — Show agent swarm status\n"
            "• Send any message to chat with the agents",
            parse_mode="Markdown",
        )

    async def _cmd_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /analyze command — create a ticket."""
        args = " ".join(context.args) if context.args else "No description provided"
        event = self.normalizer.telegram_to_event(update)

        if self.nats:
            await self.nats.publish(event)
            await update.message.reply_text(
                f"📨 Feature request received:\n_{args}_\n\nRouting to Analyst...",
                parse_mode="Markdown",
            )

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command."""
        await update.message.reply_text(
            "🤖 *Agent Swarm Status*\n\n"
            "Phase 0 — Foundation Bootstrap\n"
            "• Orchestrator: 🟢 Running\n"
            "• Analyst: 🟢 Ready\n"
            "• Developer: 🟢 Ready\n"
            "• QA: 🟢 Ready\n"
            "• PM: 🟢 Ready\n",
            parse_mode="Markdown",
        )

    async def _on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle regular text messages."""
        event = self.normalizer.telegram_to_event(update)
        if self.nats:
            await self.nats.publish(event)
            logger.debug("Message forwarded to NATS", user_id=event.user_id)
