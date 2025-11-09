"""
Service for compiling documents from PostgreSQL data for Chroma RAG.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Order,
    Campaign,
    CampaignResult,
    Consumer,
    Feedback,
    MenuEvent,
    Store,
)

logger = logging.getLogger(__name__)


def compile_order_document(order: Order) -> Dict[str, Any]:
    """Compile order data into a document for RAG."""
    products = order.products or []
    product_names = [p.get("name", "") for p in products if isinstance(p, dict)]
    product_text = ", ".join(product_names[:5])  # Limit to first 5 products

    total_price_brl = (order.total_price or 0) / 100

    doc_text = f"Order #{order.code or order.id}: Total R$ {total_price_brl:.2f}. Products: {product_text}"
    if len(product_names) > 5:
        doc_text += f" and {len(product_names) - 5} more"

    return {
        "text": doc_text,
        "metadata": {
            "store_id": order.store_id,
            "content_type": "order",
            "content_id": order.id,
            "order_code": order.code,
            "total_price": order.total_price,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        },
    }


def compile_campaign_document(campaign: Campaign) -> Dict[str, Any]:
    """Compile campaign data into a document for RAG."""
    doc_text = f"Campaign {campaign.campaign_id} ({campaign.type or 'unknown'}): Targeting {campaign.targeting or 'all'}, Status {campaign.status or 'unknown'}"

    return {
        "text": doc_text,
        "metadata": {
            "store_id": campaign.store_id,
            "content_type": "campaign",
            "content_id": campaign.id,
            "campaign_id": campaign.campaign_id,
            "type": campaign.type,
            "status": campaign.status,
            "created_at": campaign.created_at.isoformat()
            if campaign.created_at
            else None,
        },
    }


def compile_campaign_result_document(result: CampaignResult) -> Dict[str, Any]:
    """Compile campaign result data into a document for RAG."""
    send_status = result.send_status or {}
    success_count = (
        send_status.get("successCount", 0) if isinstance(send_status, dict) else 0
    )
    total_count = (
        send_status.get("totalCount", 0) if isinstance(send_status, dict) else 0
    )

    conversion_text = (
        f"{result.conversion_rate:.2f}%" if result.conversion_rate else "N/A"
    )

    doc_text = f"Campaign {result.campaign_id} Results: Sent {success_count}/{total_count}, Conversion: {conversion_text}"

    return {
        "text": doc_text,
        "metadata": {
            "store_id": result.store_id,
            "content_type": "campaign_result",
            "content_id": result.id,
            "campaign_id": result.campaign_id,
            "conversion_rate": result.conversion_rate,
            "timestamp": result.timestamp.isoformat() if result.timestamp else None,
        },
    }


def compile_consumer_document(consumer: Consumer) -> Dict[str, Any]:
    """Compile consumer data into a document for RAG."""
    preferences = consumer.preferences or {}
    pref_summary = ""
    if isinstance(preferences, dict):
        pref_items = list(preferences.items())[:3]  # First 3 preferences
        pref_summary = ", ".join([f"{k}: {v}" for k, v in pref_items])

    doc_text = f"Customer {consumer.name or 'Unknown'} ({consumer.phone or 'N/A'}): {consumer.number_of_orders or 0} orders"
    if pref_summary:
        doc_text += f". Preferences: {pref_summary}"

    return {
        "text": doc_text,
        "metadata": {
            "store_id": consumer.store_id,
            "content_type": "consumer",
            "content_id": consumer.id,
            "phone": consumer.phone,
            "name": consumer.name,
            "number_of_orders": consumer.number_of_orders,
            "last_order_date": consumer.last_order_date.isoformat()
            if consumer.last_order_date
            else None,
        },
    }


def compile_feedback_document(feedback: Feedback) -> Dict[str, Any]:
    """Compile feedback data into a document for RAG."""
    response_text = feedback.response[:100] if feedback.response else "No comment"

    doc_text = f"Feedback on order {feedback.order_id or 'N/A'}: Rating {feedback.rating or 'N/A'}/5 ({feedback.category or 'unknown'}). Comment: {response_text}"

    return {
        "text": doc_text,
        "metadata": {
            "store_id": feedback.store_id,
            "content_type": "feedback",
            "content_id": feedback.id,
            "order_id": feedback.order_id,
            "rating": feedback.rating,
            "category": feedback.category,
            "created_at": feedback.created_at.isoformat()
            if feedback.created_at
            else None,
        },
    }


def compile_menu_event_session_document(
    session_id: str, events: List[MenuEvent]
) -> Dict[str, Any]:
    """Compile menu events grouped by session into a document for RAG."""
    event_types = list(set([e.event_type for e in events if e.event_type]))
    event_count = len(events)

    doc_text = f"Session {session_id}: {event_count} events including {', '.join(event_types[:5])}"
    if len(event_types) > 5:
        doc_text += f" and {len(event_types) - 5} more event types"

    # Get timestamp range
    timestamps = [e.timestamp for e in events if e.timestamp]
    min_timestamp = min(timestamps) if timestamps else None
    max_timestamp = max(timestamps) if timestamps else None

    return {
        "text": doc_text,
        "metadata": {
            "store_id": events[0].store_id if events else "",
            "content_type": "menu_event_session",
            "content_id": session_id,
            "session_id": session_id,
            "event_count": event_count,
            "event_types": event_types,
            "min_timestamp": min_timestamp.isoformat() if min_timestamp else None,
            "max_timestamp": max_timestamp.isoformat() if max_timestamp else None,
        },
    }


def compile_store_document(store: Store) -> Dict[str, Any]:
    """Compile store data into a document for RAG."""
    raw_data = store.raw_data or {}
    address = raw_data.get("address", {})
    city = address.get("city", "") if isinstance(address, dict) else ""
    state = address.get("state", "") if isinstance(address, dict) else ""

    doc_text = f"Store {store.name} ({store.cnpj or 'N/A'}): Located in {city}, {state}"

    return {
        "text": doc_text,
        "metadata": {
            "store_id": store.id,
            "content_type": "store",
            "content_id": store.id,
            "name": store.name,
            "cnpj": store.cnpj,
            "status": store.status,
        },
    }


async def compile_all_documents_for_store(
    session: AsyncSession,
    store_id: str,
    limit_per_type: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Compile all documents for a store from PostgreSQL data.

    Args:
        session: Database session
        store_id: Store ID
        limit_per_type: Maximum documents per content type

    Returns:
        List of document dictionaries with 'text' and 'metadata'
    """
    documents = []

    # Compile orders
    stmt = select(Order).where(Order.store_id == store_id).limit(limit_per_type)
    result = await session.execute(stmt)
    orders = result.scalars().all()
    for order in orders:
        documents.append(compile_order_document(order))
    logger.info(f"Compiled {len(orders)} order documents")

    # Compile campaigns
    stmt = select(Campaign).where(Campaign.store_id == store_id).limit(limit_per_type)
    result = await session.execute(stmt)
    campaigns = result.scalars().all()
    for campaign in campaigns:
        documents.append(compile_campaign_document(campaign))
    logger.info(f"Compiled {len(campaigns)} campaign documents")

    # Compile campaign results
    stmt = (
        select(CampaignResult)
        .where(CampaignResult.store_id == store_id)
        .limit(limit_per_type)
    )
    result = await session.execute(stmt)
    results = result.scalars().all()
    for result_item in results:
        documents.append(compile_campaign_result_document(result_item))
    logger.info(f"Compiled {len(results)} campaign result documents")

    # Compile consumers
    stmt = select(Consumer).where(Consumer.store_id == store_id).limit(limit_per_type)
    result = await session.execute(stmt)
    consumers = result.scalars().all()
    for consumer in consumers:
        documents.append(compile_consumer_document(consumer))
    logger.info(f"Compiled {len(consumers)} consumer documents")

    # Compile feedbacks
    stmt = select(Feedback).where(Feedback.store_id == store_id).limit(limit_per_type)
    result = await session.execute(stmt)
    feedbacks = result.scalars().all()
    for feedback in feedbacks:
        documents.append(compile_feedback_document(feedback))
    logger.info(f"Compiled {len(feedbacks)} feedback documents")

    # Compile menu events grouped by session
    stmt = (
        select(MenuEvent)
        .where(MenuEvent.store_id == store_id)
        .limit(limit_per_type * 10)
    )
    result = await session.execute(stmt)
    events = result.scalars().all()

    # Group by session_id
    sessions: Dict[str, List[MenuEvent]] = {}
    for event in events:
        session_id = event.session_id or "unknown"
        if session_id not in sessions:
            sessions[session_id] = []
        sessions[session_id].append(event)

    # Compile session documents
    for session_id, session_events in list(sessions.items())[:limit_per_type]:
        documents.append(
            compile_menu_event_session_document(session_id, session_events)
        )
    logger.info(f"Compiled {len(sessions)} menu event session documents")

    # Compile store document
    stmt = select(Store).where(Store.id == store_id)
    result = await session.execute(stmt)
    store = result.scalar_one_or_none()
    if store:
        documents.append(compile_store_document(store))
        logger.info("Compiled store document")

    logger.info(f"Total compiled {len(documents)} documents for store {store_id}")
    return documents


__all__ = [
    "compile_order_document",
    "compile_campaign_document",
    "compile_campaign_result_document",
    "compile_consumer_document",
    "compile_feedback_document",
    "compile_menu_event_session_document",
    "compile_store_document",
    "compile_all_documents_for_store",
]
