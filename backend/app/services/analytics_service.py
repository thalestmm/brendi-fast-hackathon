"""
Analytics service for aggregating restaurant data.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

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
    # Build base filters
    base_filters = [Order.store_id == store_id]
    if start_date:
        base_filters.append(Order.created_at >= start_date)
    if end_date:
        base_filters.append(Order.created_at <= end_date)

    # Totals
    total_orders_stmt = select(func.count(Order.id)).where(and_(*base_filters))
    total_orders_result = await session.execute(total_orders_stmt)
    total_orders = int(total_orders_result.scalar() or 0)

    revenue_stmt = select(func.sum(Order.total_price)).where(and_(*base_filters))
    revenue_result = await session.execute(revenue_stmt)
    total_revenue = int(revenue_result.scalar() or 0)

    avg_order_value = (total_revenue / total_orders) if total_orders > 0 else 0

    # Determine reporting window (defaults to last 30 days)
    period_start = start_date or datetime.now(tz=timezone.utc) - timedelta(days=30)
    period_end = end_date or datetime.now(tz=timezone.utc)

    period_filters = list(base_filters)
    if not start_date:
        period_filters.append(Order.created_at >= period_start)
    if not end_date:
        period_filters.append(Order.created_at <= period_end)

    date_expr = cast(Order.created_at, Date)
    daily_orders_stmt = (
        select(
            date_expr.label("date"),
            func.count(Order.id).label("count"),
            func.sum(Order.total_price).label("revenue"),
        )
        .where(and_(*period_filters))
        .group_by(date_expr)
        .order_by(date_expr)
    )
    daily_result = await session.execute(daily_orders_stmt)
    daily_rows = daily_result.all()

    # If no recent data and no explicit date range, fall back to entire dataset
    if not daily_rows and not start_date:
        range_stmt = select(
            func.min(Order.created_at), func.max(Order.created_at)
        ).where(Order.store_id == store_id)
        range_result = await session.execute(range_stmt)
        min_created_at, max_created_at = range_result.one()

        if max_created_at:
            period_start = min_created_at or max_created_at
            period_end = max_created_at

            period_filters = list(base_filters)
            period_filters.append(Order.created_at >= period_start)
            period_filters.append(Order.created_at <= period_end)

            daily_orders_stmt = (
                select(
                    date_expr.label("date"),
                    func.count(Order.id).label("count"),
                    func.sum(Order.total_price).label("revenue"),
                )
                .where(and_(*period_filters))
                .group_by(date_expr)
                .order_by(date_expr)
            )

            daily_rows = (await session.execute(daily_orders_stmt)).all()

    daily_data = [
        {
            "date": row.date.isoformat() if row.date else None,
            "orders": row.count,
            "revenue": int(row.revenue) if row.revenue else 0,
        }
        for row in daily_rows
    ]

    # Orders by day of week
    weekday_labels = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
    dow_expr = func.extract("dow", Order.created_at)
    dow_stmt = (
        select(
            dow_expr.label("dow"),
            func.count(Order.id).label("count"),
            func.sum(Order.total_price).label("revenue"),
        )
        .where(and_(*base_filters))
        .group_by(dow_expr)
        .order_by(dow_expr)
    )
    dow_result = await session.execute(dow_stmt)
    orders_by_day_of_week = []
    for row in dow_result.all():
        dow_index = int(row.dow) if row.dow is not None else None
        label = (
            weekday_labels[dow_index]
            if dow_index is not None and 0 <= dow_index < len(weekday_labels)
            else "Desconhecido"
        )
        orders_by_day_of_week.append(
            {
                "day": label,
                "orders": row.count,
                "revenue": int(row.revenue) if row.revenue else 0,
            }
        )

    # Orders by hour of day
    hour_expr = func.extract("hour", Order.created_at)
    hour_stmt = (
        select(
            hour_expr.label("hour"),
            func.count(Order.id).label("count"),
            func.sum(Order.total_price).label("revenue"),
        )
        .where(and_(*base_filters))
        .group_by(hour_expr)
        .order_by(hour_expr)
    )
    hour_result = await session.execute(hour_stmt)
    orders_by_hour = [
        {
            "hour": int(row.hour) if row.hour is not None else 0,
            "orders": row.count,
            "revenue": int(row.revenue) if row.revenue else 0,
        }
        for row in hour_result.all()
    ]

    # Order value distribution buckets (values in cents)
    bucket_definitions = [
        ("Até R$ 50", 0, 5000),
        ("R$ 50 - R$ 99", 5000, 10000),
        ("R$ 100 - R$ 149", 10000, 15000),
        ("R$ 150 - R$ 199", 15000, 20000),
        ("R$ 200+", 20000, None),
    ]
    bucket_stats = {
        label: {"orders": 0, "revenue": 0} for label, _start, _end in bucket_definitions
    }

    value_stmt = select(Order.total_price).where(and_(*base_filters))
    value_result = await session.execute(value_stmt)
    for total_price in value_result.scalars().all():
        price = int(total_price or 0)
        for label, start_value, end_value in bucket_definitions:
            if price >= start_value and (end_value is None or price < end_value):
                bucket_stats[label]["orders"] += 1
                bucket_stats[label]["revenue"] += price
                break

    order_value_distribution = [
        {
            "bucket": label,
            "orders": stats["orders"],
            "revenue": stats["revenue"],
        }
        for label, stats in bucket_stats.items()
    ]

    # Detailed per-order analysis
    order_details_stmt = select(
        Order.products, Order.raw_data, Order.total_price
    ).where(and_(*base_filters))
    order_details_result = await session.execute(order_details_stmt)
    item_totals: Dict[str, Dict[str, int]] = {}
    status_totals: Dict[str, Dict[str, int]] = {}
    area_totals: Dict[str, Dict[str, int]] = {}

    for products, raw_data, total_price in order_details_result.all():
        order_revenue = int(total_price or 0)

        if products:
            for product in products:
                name = product.get("name") or "Item sem nome"
                quantity = int(product.get("quantity") or 0)
                price = int(product.get("price") or 0)
                stats = item_totals.setdefault(name, {"orders": 0, "revenue": 0})
                stats["orders"] += quantity
                stats["revenue"] += quantity * price

        payload = raw_data or {}
        status_key = (payload.get("status") or "desconhecido").strip().lower()
        status_label = (
            status_key.title()
            if status_key not in {"", "desconhecido"}
            else "Desconhecido"
        )
        status_stats = status_totals.setdefault(
            status_label, {"orders": 0, "revenue": 0}
        )
        status_stats["orders"] += 1
        status_stats["revenue"] += order_revenue

        delivery_info = payload.get("delivery") or {}
        address_info = delivery_info.get("address") or {}
        neighborhood = (
            address_info.get("neighborhood")
            or address_info.get("geocoderNeighborhood")
            or ""
        ).strip()
        neighborhood_label = neighborhood if neighborhood else "Não informado"
        area_stats = area_totals.setdefault(
            neighborhood_label, {"orders": 0, "revenue": 0}
        )
        area_stats["orders"] += 1
        area_stats["revenue"] += order_revenue

    top_menu_items = [
        {
            "name": name,
            "orders": stats["orders"],
            "revenue": stats["revenue"],
        }
        for name, stats in sorted(
            item_totals.items(), key=lambda item: item[1]["orders"], reverse=True
        )[:5]
    ]

    orders_by_status = [
        {
            "status": status,
            "orders": stats["orders"],
            "revenue": stats["revenue"],
        }
        for status, stats in sorted(
            status_totals.items(), key=lambda item: item[1]["orders"], reverse=True
        )
    ]

    top_delivery_areas = [
        {
            "area": area,
            "orders": stats["orders"],
            "revenue": stats["revenue"],
        }
        for area, stats in sorted(
            area_totals.items(), key=lambda item: item[1]["orders"], reverse=True
        )[:5]
    ]

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "average_order_value": avg_order_value,
        "daily_data": daily_data,
        "orders_by_day_of_week": orders_by_day_of_week,
        "orders_by_hour": orders_by_hour,
        "order_value_distribution": order_value_distribution,
        "top_menu_items": top_menu_items,
        "orders_by_status": orders_by_status,
        "top_delivery_areas": top_delivery_areas,
        "period": {
            "start": period_start.isoformat() if period_start else None,
            "end": period_end.isoformat() if period_end else None,
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
