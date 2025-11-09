"""
Chat models for AI agent conversations.
"""

from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Index, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.core.database import Base


class ChatSession(Base):
    """Chat session model for AI conversations."""

    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    store_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )

    # Relationship
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_chat_sessions_store_id", "store_id"),
        Index("idx_chat_sessions_active", "is_active"),
        Index("idx_chat_sessions_store_active", "store_id", "is_active"),
    )


class ChatMessage(Base):
    """Chat message model for conversation messages."""

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    store_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String, nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationship
    session: Mapped["ChatSession"] = relationship(
        "ChatSession", back_populates="messages"
    )

    __table_args__ = (
        Index("idx_chat_messages_session_id", "session_id"),
        Index("idx_chat_messages_store_id", "store_id"),
        Index("idx_chat_messages_created_at", "created_at"),
    )


class ChatSessionState(Base):
    """LangGraph conversation state storage."""

    __tablename__ = "chat_session_states"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    store_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    state: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_chat_session_states_session_id", "session_id"),
        Index("idx_chat_session_states_store_id", "store_id"),
    )
