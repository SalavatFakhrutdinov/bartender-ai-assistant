"""Chat session and message models."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from shared.models.user import User


class ChatSession(Base, UUIDMixin, TimestampMixin):
    """A single chat conversation."""

    __tablename__ = "chat_sessions"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(255))
    first_message: Mapped[str | None] = mapped_column(Text)
    model_used_id: Mapped[str | None] = mapped_column(
        ForeignKey("models.id"),
    )

    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )


class Message(Base, UUIDMixin, TimestampMixin):
    """Individual chat message."""

    __tablename__ = "messages"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    command: Mapped[str | None] = mapped_column(String(50))
    command_args: Mapped[dict | None] = mapped_column(JSONB)
    model_used_id: Mapped[str | None] = mapped_column(
        ForeignKey("models.id"),
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    token_count_input: Mapped[int | None] = mapped_column(Integer)
    token_count_output: Mapped[int | None] = mapped_column(Integer)

    session: Mapped["ChatSession"] = relationship(
        "ChatSession", back_populates="messages"
    )
