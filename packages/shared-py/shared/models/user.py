"""User and subscription models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMPTZ
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from shared.models.chat import ChatSession
    from shared.models.gamification import UserQuestProgress


class User(Base, UUIDMixin, TimestampMixin):
    """Application user, synced from Clerk."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    clerk_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="free",
        server_default="free",
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    launch_promo_ends_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Relationships
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession", back_populates="user", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan"
    )
    quest_progress: Mapped[list["UserQuestProgress"]] = relationship(
        "UserQuestProgress", back_populates="user"
    )

    def effective_tier(self) -> str:
        """Return effective tier considering launch promotion."""
        if self.launch_promo_ends_at and self.launch_promo_ends_at > datetime.utcnow():
            return "paid"
        if self.tier in ("paid_monthly", "paid_annual", "team"):
            return "paid"
        return "free"


class Subscription(Base, UUIDMixin, TimestampMixin):
    """Stripe subscription record."""

    __tablename__ = "subscriptions"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    stripe_sub_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    plan: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    current_period_start: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    current_period_end: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False)

    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
