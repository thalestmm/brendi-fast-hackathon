"""
Agent tools for querying analytics data.
"""

import logging
import asyncio
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


def _run_async(coro):
    """Helper to run async function in sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, create a new task
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create new one
        return asyncio.run(coro)


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
def get_order_analytics_tool(
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

    async def _get_analytics():
        async with AsyncSessionLocal() as session:
            return await get_order_analytics(
                session=session,
                store_id=store_id,
                start_date=_parse_iso_datetime(start_date),
                end_date=_parse_iso_datetime(end_date),
            )

    try:
        return _run_async(_get_analytics())
    except Exception as e:
        logger.error(f"Error getting order analytics: {e}")
        return {"error": str(e)}


@tool
def get_campaign_analytics_tool(store_id: str = "") -> Dict[str, Any]:
    """
    Get campaign analytics for a store.

    Note: store_id is automatically provided - you don't need to specify it.

    Returns:
        Dictionary with campaign analytics including total_campaigns,
        campaigns_by_status, campaigns_by_type, and average_conversion_rate
    """

    async def _get_analytics():
        async with AsyncSessionLocal() as session:
            return await get_campaign_analytics(session=session, store_id=store_id)

    try:
        return _run_async(_get_analytics())
    except Exception as e:
        logger.error(f"Error getting campaign analytics: {e}")
        return {"error": str(e)}


@tool
def get_consumer_analytics_tool(store_id: str = "") -> Dict[str, Any]:
    """
    Get consumer analytics for a store.

    Note: store_id is automatically provided - you don't need to specify it.

    Returns:
        Dictionary with consumer analytics including total_consumers,
        consumers_by_type, average_orders_per_consumer, and top_consumers
    """

    async def _get_analytics():
        async with AsyncSessionLocal() as session:
            return await get_consumer_analytics(session=session, store_id=store_id)

    try:
        return _run_async(_get_analytics())
    except Exception as e:
        logger.error(f"Error getting consumer analytics: {e}")
        return {"error": str(e)}


@tool
def get_feedback_analytics_tool(store_id: str = "") -> Dict[str, Any]:
    """
    Get customer feedback analytics for a store.

    Note: store_id is automatically provided - you don't need to specify it.

    Returns:
        Dictionary with feedback analytics including total_feedbacks,
        average_rating, feedbacks_by_category, and feedbacks_by_rating
    """

    async def _get_analytics():
        async with AsyncSessionLocal() as session:
            return await get_feedback_analytics(session=session, store_id=store_id)

    try:
        return _run_async(_get_analytics())
    except Exception as e:
        logger.error(f"Error getting feedback analytics: {e}")
        return {"error": str(e)}


@tool
def get_menu_events_analytics_tool(store_id: str = "") -> Dict[str, Any]:
    """
    Get menu events analytics for a store.

    Note: store_id is automatically provided - you don't need to specify it.

    Returns:
        Dictionary with menu events analytics including total_events,
        events_by_type, events_by_device_type, and events_by_platform
    """

    async def _get_analytics():
        async with AsyncSessionLocal() as session:
            return await get_menu_events_analytics(session=session, store_id=store_id)

    try:
        return _run_async(_get_analytics())
    except Exception as e:
        logger.error(f"Error getting menu events analytics: {e}")
        return {"error": str(e)}


@tool
def get_top_menu_items_tool(
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

    async def _get_top_menu_items():
        async with AsyncSessionLocal() as session:
            analytics = await get_order_analytics(
                session=session,
                store_id=store_id,
                start_date=_parse_iso_datetime(start_date),
                end_date=_parse_iso_datetime(end_date),
            )

            try:
                parsed_limit = int(limit)
            except (TypeError, ValueError):
                parsed_limit = 5

            if parsed_limit <= 0:
                parsed_limit = 5

            top_items = analytics.get("top_menu_items", []) or []

            return {
                "top_menu_items": top_items[:parsed_limit],
                "total_available": len(top_items),
                "limit": parsed_limit,
                "period": analytics.get("period"),
            }

    try:
        return _run_async(_get_top_menu_items())
    except Exception as e:
        logger.error(f"Error getting top menu items: {e}")
        return {"error": str(e)}


__all__ = [
    "get_order_analytics_tool",
    "get_campaign_analytics_tool",
    "get_consumer_analytics_tool",
    "get_feedback_analytics_tool",
    "get_menu_events_analytics_tool",
    "get_top_menu_items_tool",
]
