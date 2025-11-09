"""
Consumer/Customer models.
"""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Consumer(Base):
    """Consumer/Customer model."""

    __tablename__ = "consumers"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    store_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=True)
    number_of_orders: Mapped[int] = mapped_column(Integer, nullable=True)
    last_order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    preferences: Mapped[dict] = mapped_column(JSONB, nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        Index("idx_consumers_store_id", "store_id"),
        Index("idx_consumers_phone", "phone"),
        Index("idx_consumers_last_order", "last_order_date"),
        Index("idx_consumers_store_phone", "store_id", "phone"),
    )
