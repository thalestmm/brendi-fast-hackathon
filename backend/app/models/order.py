"""
Order model for restaurant orders.
"""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Order(Base):
    """Order model for restaurant orders."""

    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(String, unique=True, index=True)
    code: Mapped[str] = mapped_column(String, nullable=True, index=True)
    store_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    total_price: Mapped[int] = mapped_column(Integer, nullable=True)  # Price in cents
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    products: Mapped[dict] = mapped_column(JSONB, nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        Index("idx_orders_store_id", "store_id"),
        Index("idx_orders_created_at", "created_at"),
        Index("idx_orders_store_created", "store_id", "created_at"),
    )
