"""
Agent tools for querying analytics data.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from langchain_core.tools import tool

from app.services.analytics_service import (
    get_order_analytics,
    get_campaign_analytics,
    get_consumer_analytics,
    get_feedback_analytics,
    get_menu_events_analytics,
)
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string into datetime object if provided."""
    if not value:
        return None

    normalized = value.replace("Z", "+00:00") if "Z" in value else value
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"Invalid ISO datetime format: {value}") from exc


@tool
async def get_order_analytics_tool(
    store_id: str = "",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get order analytics for a store.

    Note: store_id is automatically provided - you don't need to specify it.

    Args:
        start_date: Start date in ISO format (optional, defaults to 30 days ago)
        end_date: End date in ISO format (optional, defaults to now)

    Returns:
        Dictionary with order analytics including total_orders, total_revenue,
        average_order_value, daily_data, top_menu_items, top_delivery_areas,
        and orders_by_status.
    """

    try:
        parsed_start = _parse_iso_datetime(start_date)
        parsed_end = _parse_iso_datetime(end_date)
    except ValueError as exc:
        logger.error(f"Invalid date provided to get_order_analytics_tool: {exc}")
        return {"error": str(exc)}

    try:
        async with AsyncSessionLocal() as session:
            return await get_order_analytics(
                session=session,
                store_id=store_id,
                start_date=parsed_start,
                end_date=parsed_end,
            )
    except Exception as exc:
        logger.error("Error getting order analytics", exc_info=True)
        return {"error": str(exc)}


@tool
async def get_campaign_analytics_tool(store_id: str = "") -> Dict[str, Any]:
    """
    Get campaign analytics for a store.

    Note: store_id is automatically provided - you don't need to specify it.

    Returns:
        Dictionary with campaign analytics including total_campaigns,
        campaigns_by_status, campaigns_by_type, and average_conversion_rate
    """

    try:
        async with AsyncSessionLocal() as session:
            return await get_campaign_analytics(session=session, store_id=store_id)
    except Exception as exc:
        logger.error("Error getting campaign analytics", exc_info=True)
        return {"error": str(exc)}


@tool
async def get_consumer_analytics_tool(store_id: str = "") -> Dict[str, Any]:
    """
    Get consumer analytics for a store.

    Note: store_id is automatically provided - you don't need to specify it.

    Returns:
        Dictionary with consumer analytics including total_consumers,
        consumers_by_type, average_orders_per_consumer, and top_consumers
    """

    try:
        async with AsyncSessionLocal() as session:
            return await get_consumer_analytics(session=session, store_id=store_id)
    except Exception as exc:
        logger.error("Error getting consumer analytics", exc_info=True)
        return {"error": str(exc)}


@tool
async def get_feedback_analytics_tool(store_id: str = "") -> Dict[str, Any]:
    """
    Get customer feedback analytics for a store.

    Note: store_id is automatically provided - you don't need to specify it.

    Returns:
        Dictionary with feedback analytics including total_feedbacks,
        average_rating, feedbacks_by_category, and feedbacks_by_rating
    """

    try:
        async with AsyncSessionLocal() as session:
            return await get_feedback_analytics(session=session, store_id=store_id)
    except Exception as exc:
        logger.error("Error getting feedback analytics", exc_info=True)
        return {"error": str(exc)}


@tool
async def get_menu_events_analytics_tool(store_id: str = "") -> Dict[str, Any]:
    """
    Get menu events analytics for a store.

    Note: store_id is automatically provided - you don't need to specify it.

    Returns:
        Dictionary with menu events analytics including total_events,
        events_by_type, events_by_device_type, and events_by_platform
    """

    try:
        async with AsyncSessionLocal() as session:
            return await get_menu_events_analytics(session=session, store_id=store_id)
    except Exception as exc:
        logger.error("Error getting menu events analytics", exc_info=True)
        return {"error": str(exc)}


@tool
async def get_top_menu_items_tool(
    store_id: str = "",
    limit: int = 5,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get the most ordered menu items for a store.

    Note: store_id is automatically provided - you don't need to specify it.

    Args:
        limit: Maximum number of menu items to return (defaults to 5)
        start_date: Optional ISO date filter (inclusive)
        end_date: Optional ISO date filter (inclusive)

    Returns:
        Dictionary with the top menu items including order counts and revenue.
    """

    try:
        parsed_start = _parse_iso_datetime(start_date)
        parsed_end = _parse_iso_datetime(end_date)
    except ValueError as exc:
        logger.error(f"Invalid date provided to get_top_menu_items_tool: {exc}")
        return {"error": str(exc)}

    try:
        parsed_limit = int(limit)
    except (TypeError, ValueError):
        parsed_limit = 5

    if parsed_limit <= 0:
        parsed_limit = 5

    try:
        async with AsyncSessionLocal() as session:
            analytics = await get_order_analytics(
                session=session,
                store_id=store_id,
                start_date=parsed_start,
                end_date=parsed_end,
            )

        top_items = analytics.get("top_menu_items", []) or []

        return {
            "top_menu_items": top_items[:parsed_limit],
            "total_available": len(top_items),
            "limit": parsed_limit,
            "period": analytics.get("period"),
        }
    except Exception as exc:
        logger.error("Error getting top menu items", exc_info=True)
        return {"error": str(exc)}


__all__ = [
    "get_order_analytics_tool",
    "get_campaign_analytics_tool",
    "get_consumer_analytics_tool",
    "get_feedback_analytics_tool",
    "get_menu_events_analytics_tool",
    "get_top_menu_items_tool",
]
