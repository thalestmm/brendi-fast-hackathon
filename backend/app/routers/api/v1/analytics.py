"""
Analytics API endpoints.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query, HTTPException, status

from app.core.dependencies import DbSession, StoreId
from app.schemas.api.v1.analytics import (
    OrderAnalyticsResponse,
    CampaignAnalyticsResponse,
    ConsumerAnalyticsResponse,
    FeedbackAnalyticsResponse,
    InsightRequest,
    InsightResponse,
)
from app.services.analytics_service import (
    get_order_analytics,
    get_campaign_analytics,
    get_consumer_analytics,
    get_feedback_analytics,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/orders", response_model=OrderAnalyticsResponse)
async def get_orders_analytics(
    store_id: StoreId,
    db: DbSession,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
) -> OrderAnalyticsResponse:
    """Get order analytics for a store."""
    try:
        start_dt = (
            datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if start_date
            else None
        )
        end_dt = (
            datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            if end_date
            else None
        )

        analytics = await get_order_analytics(db, store_id, start_dt, end_dt)
        return OrderAnalyticsResponse(**analytics)
    except Exception as e:
        logger.error(f"Error fetching order analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch order analytics",
        )


@router.get("/campaigns", response_model=CampaignAnalyticsResponse)
async def get_campaigns_analytics(
    store_id: StoreId,
    db: DbSession,
) -> CampaignAnalyticsResponse:
    """Get campaign analytics for a store."""
    try:
        analytics = await get_campaign_analytics(db, store_id)
        return CampaignAnalyticsResponse(**analytics)
    except Exception as e:
        logger.error(f"Error fetching campaign analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch campaign analytics",
        )


@router.get("/consumers", response_model=ConsumerAnalyticsResponse)
async def get_consumers_analytics(
    store_id: StoreId,
    db: DbSession,
) -> ConsumerAnalyticsResponse:
    """Get consumer analytics for a store."""
    try:
        analytics = await get_consumer_analytics(db, store_id)
        return ConsumerAnalyticsResponse(**analytics)
    except Exception as e:
        logger.error(f"Error fetching consumer analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch consumer analytics",
        )


@router.get("/feedbacks", response_model=FeedbackAnalyticsResponse)
async def get_feedbacks_analytics(
    store_id: StoreId,
    db: DbSession,
) -> FeedbackAnalyticsResponse:
    """Get feedback analytics for a store."""
    try:
        analytics = await get_feedback_analytics(db, store_id)
        return FeedbackAnalyticsResponse(**analytics)
    except Exception as e:
        logger.error(f"Error fetching feedback analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feedback analytics",
        )


@router.post("/insights", response_model=InsightResponse)
async def get_insights(
    store_id: StoreId,
    db: DbSession,
    request: InsightRequest,
) -> InsightResponse:
    """
    Get AI-generated insights for a dashboard page.

    TODO: Integrate with LangGraph agent to generate insights.
    For now, returns a placeholder response.
    """
    # TODO: Implement actual insight generation using LangGraph agent
    # This should query RAG service and generate insights based on analytics data

    placeholder_insights = {
        "orders": "Your order volume has been consistent. Consider analyzing peak hours to optimize staffing.",
        "campaigns": "Campaign performance varies by type. Email campaigns show higher conversion rates.",
        "consumers": "You have a strong base of repeat customers. Focus on retention strategies.",
    }

    insight_text = placeholder_insights.get(
        request.page_type, "No insights available for this page type."
    )

    return InsightResponse(
        insight=insight_text,
        page_type=request.page_type,
        generated_at=datetime.now(),
    )
