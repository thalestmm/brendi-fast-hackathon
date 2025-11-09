"""
Feedback model for customer feedback.
"""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Feedback(Base):
    """Customer feedback model."""

    __tablename__ = "feedbacks"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    store_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    store_consumer_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    order_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    category: Mapped[str] = mapped_column(String, nullable=True, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=True)
    response: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        Index("idx_feedbacks_store_id", "store_id"),
        Index("idx_feedbacks_order_id", "order_id"),
        Index("idx_feedbacks_category", "category"),
        Index("idx_feedbacks_created_at", "created_at"),
        Index("idx_feedbacks_store_created", "store_id", "created_at"),
    )
