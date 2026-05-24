"""Cocktail and feedback models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMPTZ, VECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from shared.models.llm import Model as LLMModel
    from shared.models.user import User


class Cocktail(Base, UUIDMixin, TimestampMixin):
    """Cocktail recipe, whether IBA official, AI-generated, or user-created."""

    __tablename__ = "cocktails"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    ingredients: Mapped[dict] = mapped_column(JSONB, nullable=False)
    method: Mapped[str | None] = mapped_column(Text)
    glass: Mapped[str | None] = mapped_column(String(100))
    garnish: Mapped[str | None] = mapped_column(String(255))
    tasting_notes: Mapped[dict | None] = mapped_column(JSONB)
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="generated",
        server_default="generated",
    )
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    taste_score: Mapped[float | None] = mapped_column(DECIMAL(3, 2))
    feedback_count: Mapped[int] = mapped_column(Integer, default=0)
    is_deprecated: Mapped[bool] = mapped_column(default=False)
    is_promoted: Mapped[bool] = mapped_column(default=False)
    physical_validation_status: Mapped[str | None] = mapped_column(String(20))
    qdrant_point_id: Mapped[str | None] = mapped_column(String(255))
    neo4j_node_id: Mapped[str | None] = mapped_column(String(255))
    model_used_id: Mapped[str | None] = mapped_column(ForeignKey("models.id"))
    generation_metadata: Mapped[dict | None] = mapped_column(JSONB)

    feedback: Mapped[list["CocktailFeedback"]] = relationship(
        "CocktailFeedback", back_populates="cocktail"
    )


class CocktailFeedback(Base, UUIDMixin, TimestampMixin):
    """Structured taste feedback for a cocktail."""

    __tablename__ = "cocktail_feedback"

    cocktail_id: Mapped[str] = mapped_column(ForeignKey("cocktails.id"))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    overall_rating: Mapped[int | None] = mapped_column(
        Integer, CheckConstraint("overall_rating BETWEEN 1 AND 5")
    )
    balance_rating: Mapped[int | None] = mapped_column(
        Integer, CheckConstraint("balance_rating BETWEEN 1 AND 5")
    )
    aroma_rating: Mapped[int | None] = mapped_column(
        Integer, CheckConstraint("aroma_rating BETWEEN 1 AND 5")
    )
    appearance_rating: Mapped[int | None] = mapped_column(
        Integer, CheckConstraint("appearance_rating BETWEEN 1 AND 5")
    )
    guest_reaction: Mapped[int | None] = mapped_column(
        Integer, CheckConstraint("guest_reaction BETWEEN 1 AND 5")
    )
    would_repeat: Mapped[str | None] = mapped_column(String(20))
    modification_note: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(VECTOR(1536))

    cocktail: Mapped["Cocktail"] = relationship("Cocktail", back_populates="feedback")
