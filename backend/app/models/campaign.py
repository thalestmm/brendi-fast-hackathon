"""
Campaign models for marketing campaigns.
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Float, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Campaign(Base):
    """Campaign model for marketing campaigns."""

    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    campaign_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    store_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=True, index=True)
    targeting: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        Index("idx_campaigns_store_id", "store_id"),
        Index("idx_campaigns_campaign_id", "campaign_id"),
        Index("idx_campaigns_store_campaign", "store_id", "campaign_id"),
        Index("idx_campaigns_created_at", "created_at"),
    )


class CampaignResult(Base):
    """Campaign result/metrics model."""

    __tablename__ = "campaign_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    campaign_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    store_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    conversion_rate: Mapped[float] = mapped_column(Float, nullable=True)
    send_status: Mapped[dict] = mapped_column(JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        Index("idx_campaign_results_store_id", "store_id"),
        Index("idx_campaign_results_campaign_id", "campaign_id"),
        Index("idx_campaign_results_timestamp", "timestamp"),
        Index("idx_campaign_results_store_campaign", "store_id", "campaign_id"),
    )
