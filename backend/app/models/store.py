"""
Store model for restaurant/store information.
"""

from sqlalchemy import String, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Store(Base):
    """Store/Restaurant information model."""

    __tablename__ = "stores"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    cnpj: Mapped[str] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        Index("idx_stores_id", "id"),
        Index("idx_stores_uuid", "uuid"),
    )
