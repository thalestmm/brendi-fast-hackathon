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

    Uses LangGraph agent with RAG context to generate actionable insights.
    Results are cached for 5 minutes to improve performance.
    """
    from app.graphs.insights import generate_insight_for_page
    from app.services.cache_service import get_cache_service

    cache_service = get_cache_service()

    try:
        # Check cache first
        cached_data = await cache_service.get_insight(
            store_id=store_id,
            page_type=request.page_type,
        )

        if cached_data:
            logger.info(f"Returning cached insight for {store_id}:{request.page_type}")
            return InsightResponse(
                insight=cached_data["insight"],
                page_type=cached_data["page_type"],
                generated_at=datetime.fromisoformat(cached_data["generated_at"]),
            )

        # Generate new insight if not cached
        logger.info(f"Generating new insight for {store_id}:{request.page_type}")
        insight_text = await generate_insight_for_page(
            store_id=store_id,
            page_type=request.page_type,
        )

        # Cache the result
        await cache_service.set_insight(
            store_id=store_id,
            page_type=request.page_type,
            insight=insight_text,
            ttl=300,  # 5 minutes TTL
        )

        return InsightResponse(
            insight=insight_text,
            page_type=request.page_type,
            generated_at=datetime.now(),
        )
    except Exception as e:
        logger.error(f"Error generating insights: {e}", exc_info=True)
        # Return fallback insight
        return InsightResponse(
            insight="Unable to generate insights at this time. Please try again later.",
            page_type=request.page_type,
            generated_at=datetime.now(),
        )


@router.delete("/insights/cache")
async def clear_insights_cache(
    store_id: StoreId,
) -> dict:
    """
    Clear all cached insights for a store.

    This endpoint allows administrators to invalidate the cache
    when needed (e.g., after data updates).
    """
    from app.services.cache_service import get_cache_service

    cache_service = get_cache_service()

    try:
        deleted_count = await cache_service.clear_store_insights(store_id)
        logger.info(f"Cleared {deleted_count} cached insights for store {store_id}")

        return {
            "status": "success",
            "message": f"Cleared {deleted_count} cached insights",
            "store_id": store_id,
        }
    except Exception as e:
        logger.error(f"Error clearing insights cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear insights cache",
        )
