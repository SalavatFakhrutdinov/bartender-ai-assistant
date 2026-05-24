"""LLM registry, usage tracking, bar context, and pending cocktails."""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import DECIMAL, JSONB, TIMESTAMPTZ
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base, TimestampMixin, UUIDMixin


class Model(Base, UUIDMixin, TimestampMixin):
    """Normalized LLM model registry."""

    __tablename__ = "models"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="free",
        server_default="free",
    )
    max_tokens: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(default=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB)


class LLMUsage(Base, UUIDMixin, TimestampMixin):
    """Per-request LLM usage and cost tracking."""

    __tablename__ = "llm_usage"

    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[str | None] = mapped_column(ForeignKey("chat_sessions.id"))
    model_used_id: Mapped[str] = mapped_column(
        ForeignKey("models.id"),
        nullable=False,
    )
    tokens_input: Mapped[int] = mapped_column(Integer, nullable=False)
    tokens_output: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[float | None] = mapped_column(DECIMAL(8, 6))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    cached: Mapped[bool] = mapped_column(default=False)


class UserBarContext(Base, UUIDMixin, TimestampMixin):
    """Paid-user bar concept, inventory, and uploaded documents."""

    __tablename__ = "user_bar_context"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    concept_text: Mapped[str | None] = mapped_column(Text)
    inventory: Mapped[dict | None] = mapped_column(JSONB)
    style_preferences: Mapped[dict | None] = mapped_column(JSONB)
    target_price_range: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    uploaded_docs: Mapped[dict | None] = mapped_column(JSONB)
    qdrant_namespace: Mapped[str | None] = mapped_column(String(100))


class PendingCocktail(Base, UUIDMixin, TimestampMixin):
    """Scraped or submitted cocktails awaiting admin curation."""

    __tablename__ = "pending_cocktails"

    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500))
    source_type: Mapped[str | None] = mapped_column(String(50))
    quality_rating: Mapped[int | None] = mapped_column(
        Integer,
        CheckConstraint("quality_rating BETWEEN 1 AND 5"),
    )
    taste_score: Mapped[float | None] = mapped_column(DECIMAL(3, 2))
    approved_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    status: Mapped[str] = mapped_column(String(20), default="pending")
