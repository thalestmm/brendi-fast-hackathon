"""
Analytics API schemas.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class DailyData(BaseModel):
    """Daily analytics data point."""

    date: Optional[str]
    orders: int
    revenue: int


class DayOfWeekData(BaseModel):
    """Aggregated orders by day of week."""

    day: str
    orders: int
    revenue: int


class HourlyData(BaseModel):
    """Aggregated orders by hour."""

    hour: int
    orders: int
    revenue: int


class OrderValueBucket(BaseModel):
    """Order value distribution bucket."""

    bucket: str
    orders: int
    revenue: int


class TopMenuItem(BaseModel):
    """Top selling menu items."""

    name: str
    orders: int
    revenue: int


class OrderAnalyticsResponse(BaseModel):
    """Order analytics response."""

    total_orders: int
    total_revenue: int
    average_order_value: float
    daily_data: List[DailyData]
    orders_by_day_of_week: List[DayOfWeekData]
    orders_by_hour: List[HourlyData]
    order_value_distribution: List[OrderValueBucket]
    top_menu_items: List[TopMenuItem]
    period: Dict[str, Optional[str]]


class CampaignAnalyticsResponse(BaseModel):
    """Campaign analytics response."""

    total_campaigns: int
    campaigns_by_status: Dict[str, int]
    campaigns_by_type: Dict[str, int]
    average_conversion_rate: float


class TopCustomer(BaseModel):
    """Top customer information."""

    id: str
    name: Optional[str]
    phone: Optional[str]
    order_count: Optional[int]


class ConsumerAnalyticsResponse(BaseModel):
    """Consumer analytics response."""

    total_consumers: int
    average_orders_per_consumer: float
    top_customers: List[TopCustomer]


class CategoryFeedback(BaseModel):
    """Feedback by category."""

    count: int
    average_rating: float


class FeedbackAnalyticsResponse(BaseModel):
    """Feedback analytics response."""

    total_feedbacks: int
    average_rating: float
    feedbacks_by_category: Dict[str, CategoryFeedback]


class InsightRequest(BaseModel):
    """Request for AI-generated insights."""

    page_type: str = Field(
        ..., description="Type of dashboard page (orders, campaigns, consumers)"
    )
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context for insight generation"
    )


class InsightResponse(BaseModel):
    """AI-generated insight response."""

    insight: str
    page_type: str
    generated_at: datetime
