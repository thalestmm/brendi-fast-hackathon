"""
Analytics service for aggregating restaurant data.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from sqlalchemy import select, func, and_, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, Campaign, CampaignResult, Consumer, Feedback, MenuEvent

logger = logging.getLogger(__name__)


async def get_order_analytics(
    session: AsyncSession,
    store_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Get order analytics for a store.

    Args:
        session: Database session
        store_id: Store ID
        start_date: Start date filter
        end_date: End date filter

    Returns:
        Dictionary with order analytics
    """
    # Build query
    conditions = [Order.store_id == store_id]
    if start_date:
        conditions.append(Order.created_at >= start_date)
    if end_date:
        conditions.append(Order.created_at <= end_date)

    # Total orders
    total_orders_stmt = select(func.count(Order.id)).where(and_(*conditions))
    total_orders_result = await session.execute(total_orders_stmt)
    total_orders = total_orders_result.scalar() or 0

    # Total revenue
    revenue_stmt = select(func.sum(Order.total_price)).where(and_(*conditions))
    revenue_result = await session.execute(revenue_stmt)
    total_revenue = revenue_result.scalar() or 0

    # Average order value
    avg_order_value = (total_revenue / total_orders) if total_orders > 0 else 0

    # Orders by day (last 30 days if no date range)
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()

    # Use CAST to DATE for PostgreSQL compatibility
    # This avoids GROUP BY issues with date_trunc expressions
    date_expr = cast(Order.created_at, Date)

    daily_orders_stmt = (
        select(
            date_expr.label("date"),
            func.count(Order.id).label("count"),
            func.sum(Order.total_price).label("revenue"),
        )
        .where(and_(*conditions))
        .group_by(date_expr)
        .order_by(date_expr)
    )

    daily_result = await session.execute(daily_orders_stmt)
    daily_data = [
        {
            "date": row.date.isoformat() if row.date else None,
            "orders": row.count,
            "revenue": int(row.revenue) if row.revenue else 0,
        }
        for row in daily_result.all()
    ]

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "average_order_value": avg_order_value,
        "daily_data": daily_data,
        "period": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None,
        },
    }


async def get_campaign_analytics(
    session: AsyncSession,
    store_id: str,
) -> Dict[str, Any]:
    """
    Get campaign analytics for a store.

    Args:
        session: Database session
        store_id: Store ID

    Returns:
        Dictionary with campaign analytics
    """
    # Total campaigns
    total_campaigns_stmt = select(func.count(Campaign.id)).where(
        Campaign.store_id == store_id
    )
    total_campaigns_result = await session.execute(total_campaigns_stmt)
    total_campaigns = total_campaigns_result.scalar() or 0

    # Campaigns by status
    status_stmt = (
        select(Campaign.status, func.count(Campaign.id).label("count"))
        .where(Campaign.store_id == store_id)
        .group_by(Campaign.status)
    )

    status_result = await session.execute(status_stmt)
    campaigns_by_status = {
        row.status or "unknown": row.count for row in status_result.all()
    }

    # Campaigns by type
    type_stmt = (
        select(Campaign.type, func.count(Campaign.id).label("count"))
        .where(Campaign.store_id == store_id)
        .group_by(Campaign.type)
    )

    type_result = await session.execute(type_stmt)
    campaigns_by_type = {row.type or "unknown": row.count for row in type_result.all()}

    # Average conversion rate from campaign results
    conversion_stmt = select(func.avg(CampaignResult.conversion_rate)).where(
        CampaignResult.store_id == store_id, CampaignResult.conversion_rate.isnot(None)
    )

    conversion_result = await session.execute(conversion_stmt)
    avg_conversion_rate = conversion_result.scalar() or 0

    return {
        "total_campaigns": total_campaigns,
        "campaigns_by_status": campaigns_by_status,
        "campaigns_by_type": campaigns_by_type,
        "average_conversion_rate": float(avg_conversion_rate)
        if avg_conversion_rate
        else 0,
    }


async def get_consumer_analytics(
    session: AsyncSession,
    store_id: str,
) -> Dict[str, Any]:
    """
    Get consumer analytics for a store.

    Args:
        session: Database session
        store_id: Store ID

    Returns:
        Dictionary with consumer analytics
    """
    # Total consumers
    total_stmt = select(func.count(Consumer.id)).where(Consumer.store_id == store_id)
    total_result = await session.execute(total_stmt)
    total_consumers = total_result.scalar() or 0

    # Average orders per consumer
    avg_orders_stmt = select(func.avg(Consumer.number_of_orders)).where(
        Consumer.store_id == store_id, Consumer.number_of_orders.isnot(None)
    )
    avg_orders_result = await session.execute(avg_orders_stmt)
    avg_orders_per_consumer = avg_orders_result.scalar() or 0

    # Top customers by order count
    top_customers_stmt = (
        select(
            Consumer.id,
            Consumer.name,
            Consumer.phone,
            Consumer.number_of_orders,
        )
        .where(Consumer.store_id == store_id, Consumer.number_of_orders.isnot(None))
        .order_by(Consumer.number_of_orders.desc())
        .limit(10)
    )

    top_customers_result = await session.execute(top_customers_stmt)
    top_customers = [
        {
            "id": row.id,
            "name": row.name,
            "phone": row.phone,
            "order_count": row.number_of_orders,
        }
        for row in top_customers_result.all()
    ]

    return {
        "total_consumers": total_consumers,
        "average_orders_per_consumer": float(avg_orders_per_consumer)
        if avg_orders_per_consumer
        else 0,
        "top_customers": top_customers,
    }


async def get_feedback_analytics(
    session: AsyncSession,
    store_id: str,
) -> Dict[str, Any]:
    """
    Get feedback analytics for a store.

    Args:
        session: Database session
        store_id: Store ID

    Returns:
        Dictionary with feedback analytics
    """
    # Total feedbacks
    total_stmt = select(func.count(Feedback.id)).where(Feedback.store_id == store_id)
    total_result = await session.execute(total_stmt)
    total_feedbacks = total_result.scalar() or 0

    # Average rating
    avg_rating_stmt = select(func.avg(Feedback.rating)).where(
        Feedback.store_id == store_id, Feedback.rating.isnot(None)
    )
    avg_rating_result = await session.execute(avg_rating_stmt)
    avg_rating = avg_rating_result.scalar() or 0

    # Feedbacks by category
    category_stmt = (
        select(
            Feedback.category,
            func.count(Feedback.id).label("count"),
            func.avg(Feedback.rating).label("avg_rating"),
        )
        .where(Feedback.store_id == store_id)
        .group_by(Feedback.category)
    )

    category_result = await session.execute(category_stmt)
    feedbacks_by_category = {
        row.category or "unknown": {
            "count": row.count,
            "average_rating": float(row.avg_rating) if row.avg_rating else 0,
        }
        for row in category_result.all()
    }

    return {
        "total_feedbacks": total_feedbacks,
        "average_rating": float(avg_rating) if avg_rating else 0,
        "feedbacks_by_category": feedbacks_by_category,
    }


async def get_menu_events_analytics(
    session: AsyncSession,
    store_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Get menu interaction analytics for a store.

    Args:
        session: Database session
        store_id: Store ID
        start_date: Optional start datetime filter
        end_date: Optional end datetime filter

    Returns:
        Dictionary with menu event analytics
    """
    conditions = [MenuEvent.store_id == store_id]

    if start_date:
        conditions.append(MenuEvent.timestamp >= start_date)
    if end_date:
        conditions.append(MenuEvent.timestamp <= end_date)

    total_stmt = select(func.count(MenuEvent.id)).where(and_(*conditions))
    total_result = await session.execute(total_stmt)
    total_events = total_result.scalar() or 0

    events_by_type_stmt = (
        select(
            MenuEvent.event_type,
            func.count(MenuEvent.id).label("count"),
        )
        .where(and_(*conditions))
        .group_by(MenuEvent.event_type)
    )
    events_by_type_result = await session.execute(events_by_type_stmt)
    events_by_type = {
        (row.event_type or "unknown"): row.count for row in events_by_type_result.all()
    }

    events_by_device_stmt = (
        select(
            MenuEvent.device_type,
            func.count(MenuEvent.id).label("count"),
        )
        .where(and_(*conditions))
        .group_by(MenuEvent.device_type)
    )
    events_by_device_result = await session.execute(events_by_device_stmt)
    events_by_device_type = {
        (row.device_type or "unknown"): row.count
        for row in events_by_device_result.all()
    }

    events_by_platform_stmt = (
        select(
            MenuEvent.platform,
            func.count(MenuEvent.id).label("count"),
        )
        .where(and_(*conditions))
        .group_by(MenuEvent.platform)
    )
    events_by_platform_result = await session.execute(events_by_platform_stmt)
    events_by_platform = {
        (row.platform or "unknown"): row.count
        for row in events_by_platform_result.all()
    }

    # Default to last 30 days for period reporting if not provided
    period_start = start_date or (datetime.now() - timedelta(days=30))
    period_end = end_date or datetime.now()

    return {
        "total_events": total_events,
        "events_by_type": events_by_type,
        "events_by_device_type": events_by_device_type,
        "events_by_platform": events_by_platform,
        "period": {
            "start": period_start.isoformat() if period_start else None,
            "end": period_end.isoformat() if period_end else None,
        },
    }


__all__ = [
    "get_order_analytics",
    "get_campaign_analytics",
    "get_consumer_analytics",
    "get_feedback_analytics",
    "get_menu_events_analytics",
]
