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


@tool
def get_order_analytics_tool(
    store_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get order analytics for a store.
    
    Args:
        store_id: Store identifier
        start_date: Start date in ISO format (optional, defaults to 30 days ago)
        end_date: End date in ISO format (optional, defaults to now)
    
    Returns:
        Dictionary with order analytics including total_orders, total_revenue, 
        average_order_value, and daily_data
    """
    async def _get_analytics():
        async with AsyncSessionLocal() as session:
            start_dt = None
            end_dt = None
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            
            return await get_order_analytics(
                session=session,
                store_id=store_id,
                start_date=start_dt,
                end_date=end_dt,
            )
    
    try:
        return _run_async(_get_analytics())
    except Exception as e:
        logger.error(f"Error getting order analytics: {e}")
        return {"error": str(e)}


@tool
def get_campaign_analytics_tool(store_id: str) -> Dict[str, Any]:
    """
    Get campaign analytics for a store.
    
    Args:
        store_id: Store identifier
    
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
def get_consumer_analytics_tool(store_id: str) -> Dict[str, Any]:
    """
    Get consumer analytics for a store.
    
    Args:
        store_id: Store identifier
    
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
def get_feedback_analytics_tool(store_id: str) -> Dict[str, Any]:
    """
    Get customer feedback analytics for a store.
    
    Args:
        store_id: Store identifier
    
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
def get_menu_events_analytics_tool(store_id: str) -> Dict[str, Any]:
    """
    Get menu events analytics for a store.
    
    Args:
        store_id: Store identifier
    
    Returns:
        Dictionary with menu events analytics including total_events,
        events_by_type, events_by_device_type, and events_by_platform
    """
    async def _get_analytics():
        async with AsyncSessionLocal() as session:
            return await get_menu_events_analytics(
                session=session, store_id=store_id
            )
    
    try:
        return _run_async(_get_analytics())
    except Exception as e:
        logger.error(f"Error getting menu events analytics: {e}")
        return {"error": str(e)}


__all__ = [
    "get_order_analytics_tool",
    "get_campaign_analytics_tool",
    "get_consumer_analytics_tool",
    "get_feedback_analytics_tool",
    "get_menu_events_analytics_tool",
]
