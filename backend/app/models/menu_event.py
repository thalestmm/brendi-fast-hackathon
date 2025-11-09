"""
Menu event model for menu interaction tracking.
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MenuEvent(Base):
    """Menu interaction event model."""

    __tablename__ = "menu_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    store_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    device_type: Mapped[str] = mapped_column(String, nullable=True)
    platform: Mapped[str] = mapped_column(String, nullable=True)
    event_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        Index("idx_menu_events_store_id", "store_id"),
        Index("idx_menu_events_event_type", "event_type"),
        Index("idx_menu_events_session_id", "session_id"),
        Index("idx_menu_events_timestamp", "timestamp"),
        Index("idx_menu_events_store_timestamp", "store_id", "timestamp"),
        Index("idx_menu_events_store_event", "store_id", "event_type"),
    )
