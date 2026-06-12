"""Gamification quest models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMPTZ
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from shared.models.user import User


class Quest(Base, UUIDMixin, TimestampMixin):
    """Quest definition."""

    __tablename__ = "quests"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    quest_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_count: Mapped[int] = mapped_column(Integer, default=1)
    reward_days: Mapped[int] = mapped_column(Integer, default=7)
    is_active: Mapped[bool] = mapped_column(default=True)

    progress: Mapped[list["UserQuestProgress"]] = relationship(
        "UserQuestProgress", back_populates="quest"
    )


class UserQuestProgress(Base, UUIDMixin, TimestampMixin):
    """Per-user quest progress tracking."""

    __tablename__ = "user_quest_progress"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    quest_id: Mapped[str] = mapped_column(
        ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=False,
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(default=False)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)

    quest: Mapped["Quest"] = relationship("Quest", back_populates="progress")
    user: Mapped["User"] = relationship("User", back_populates="quest_progress")

    __table_args__ = (UniqueConstraint("user_id", "quest_id", name="uq_user_quest"),)
