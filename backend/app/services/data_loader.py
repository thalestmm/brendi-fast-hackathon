"""
Data ingestion service for loading JSON files into PostgreSQL.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models import (
    Store,
    Order,
    Campaign,
    CampaignResult,
    Consumer,
    Feedback,
    MenuEvent,
)

logger = logging.getLogger(__name__)


def parse_date(date_obj: Any) -> Optional[datetime]:
    """Parse date object from JSON (handles _date.iso format)."""
    if isinstance(date_obj, dict) and date_obj.get("_date"):
        iso_str = date_obj.get("iso")
        if iso_str:
            try:
                return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            except Exception as e:
                logger.warning(f"Error parsing date {iso_str}: {e}")
                return None
    elif isinstance(date_obj, str):
        try:
            return datetime.fromisoformat(date_obj.replace("Z", "+00:00"))
        except Exception:
            pass
    return None


def parse_json_string(json_str: str) -> Dict[str, Any]:
    """Parse JSON string to dict."""
    try:
        return json.loads(json_str) if json_str else {}
    except Exception as e:
        logger.warning(f"Error parsing JSON string: {e}")
        return {}


async def load_store_data(session: AsyncSession, file_path: Path, store_id: str) -> int:
    """
    Load store data from JSON file.

    Args:
        session: Database session
        file_path: Path to store.json file
        store_id: Store ID to use

    Returns:
        Number of records loaded
    """
    logger.info(f"Loading store data from {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract fields
    store_data = {
        "id": data.get("id") or store_id,
        "uuid": data.get("uuid", ""),
        "name": data.get("name", ""),
        "cnpj": data.get("cnpj"),
        "status": data.get("status", {}).get("title")
        if isinstance(data.get("status"), dict)
        else data.get("status"),
        "raw_data": data,  # Store complete original data
    }

    # Upsert store
    stmt = insert(Store).values(**store_data)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "uuid": stmt.excluded.uuid,
            "name": stmt.excluded.name,
            "cnpj": stmt.excluded.cnpj,
            "status": stmt.excluded.status,
            "raw_data": stmt.excluded.raw_data,
        },
    )

    await session.execute(stmt)
    await session.commit()

    logger.info(f"Loaded 1 store record")
    return 1


async def load_orders_data(
    session: AsyncSession,
    file_path: Path,
    store_id: str,
    batch_size: int = 1000,
) -> int:
    """
    Load orders data from JSON file.

    Args:
        session: Database session
        file_path: Path to orders.json file
        store_id: Store ID
        batch_size: Number of orders to insert per batch

    Returns:
        Number of records loaded
    """
    logger.info(f"Loading orders data from {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        orders = json.load(f)

    if not isinstance(orders, list):
        logger.error("Orders data must be a list")
        return 0

    total_loaded = 0

    for i in range(0, len(orders), batch_size):
        batch = orders[i : i + batch_size]
        order_records = []

        for order in batch:
            created_at = parse_date(order.get("createdAt"))

            order_data = {
                "id": order.get("id", ""),
                "uuid": order.get("uuid", ""),
                "code": order.get("code"),
                "store_id": store_id,
                "total_price": order.get("totalPrice"),
                "created_at": created_at,
                "products": order.get("products", []),
                "raw_data": order,  # Store complete original data
            }
            order_records.append(order_data)

        if order_records:
            stmt = insert(Order).values(order_records)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "uuid": stmt.excluded.uuid,
                    "code": stmt.excluded.code,
                    "total_price": stmt.excluded.total_price,
                    "created_at": stmt.excluded.created_at,
                    "products": stmt.excluded.products,
                    "raw_data": stmt.excluded.raw_data,
                },
            )
            await session.execute(stmt)
            await session.commit()

            total_loaded += len(order_records)
            logger.info(
                f"Loaded batch {i // batch_size + 1}: {len(order_records)} orders (total: {total_loaded})"
            )

    logger.info(f"Loaded {total_loaded} orders total")
    return total_loaded


async def load_campaigns_data(
    session: AsyncSession,
    file_path: Path,
    store_id: str,
) -> int:
    """Load campaigns data from JSON file."""
    logger.info(f"Loading campaigns data from {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        campaigns = json.load(f)

    if not isinstance(campaigns, list):
        logger.error("Campaigns data must be a list")
        return 0

    campaign_records = []

    for campaign in campaigns:
        created_at = parse_date(campaign.get("created_at"))
        updated_at = parse_date(campaign.get("updated_at"))

        campaign_data = {
            "id": campaign.get("id", ""),
            "campaign_id": campaign.get("campaign_id", ""),
            "store_id": store_id,
            "type": campaign.get("type"),
            "targeting": campaign.get("targeting"),
            "status": campaign.get("status"),
            "created_at": created_at,
            "updated_at": updated_at,
            "raw_data": campaign,
        }
        campaign_records.append(campaign_data)

    if campaign_records:
        stmt = insert(Campaign).values(campaign_records)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "campaign_id": stmt.excluded.campaign_id,
                "type": stmt.excluded.type,
                "targeting": stmt.excluded.targeting,
                "status": stmt.excluded.status,
                "created_at": stmt.excluded.created_at,
                "updated_at": stmt.excluded.updated_at,
                "raw_data": stmt.excluded.raw_data,
            },
        )
        await session.execute(stmt)
        await session.commit()

    logger.info(f"Loaded {len(campaign_records)} campaigns")
    return len(campaign_records)


async def load_campaign_results_data(
    session: AsyncSession,
    file_path: Path,
    store_id: str,
) -> int:
    """Load campaign results data from JSON file."""
    logger.info(f"Loading campaign results data from {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    if not isinstance(results, list):
        logger.error("Campaign results data must be a list")
        return 0

    result_records = []

    for result in results:
        timestamp = parse_date(result.get("created_at")) or parse_date(
            result.get("timestamp")
        )

        # Extract conversion rate from metadata if available
        conversion_rate = result.get("conversion_rate")
        if conversion_rate is None:
            # Try to extract from metadata
            metadata = result.get("metadata", {})
            if isinstance(metadata, dict):
                conversion_rate = metadata.get("conversion_rate")

        result_data = {
            "id": result.get("id", ""),
            "campaign_id": result.get("campaign_id", ""),
            "store_id": store_id,
            "conversion_rate": conversion_rate,
            "send_status": result.get("send_status") or result.get("status"),
            "timestamp": timestamp,
            "raw_data": result,
        }
        result_records.append(result_data)

    if result_records:
        stmt = insert(CampaignResult).values(result_records)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "campaign_id": stmt.excluded.campaign_id,
                "conversion_rate": stmt.excluded.conversion_rate,
                "send_status": stmt.excluded.send_status,
                "timestamp": stmt.excluded.timestamp,
                "raw_data": stmt.excluded.raw_data,
            },
        )
        await session.execute(stmt)
        await session.commit()

    logger.info(f"Loaded {len(result_records)} campaign results")
    return len(result_records)


async def load_consumers_data(
    session: AsyncSession,
    file_path: Path,
    store_id: str,
) -> int:
    """Load consumers data from JSON file."""
    logger.info(f"Loading consumers data from {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        consumers = json.load(f)

    if not isinstance(consumers, list):
        logger.error("Consumers data must be a list")
        return 0

    consumer_records = []

    for consumer in consumers:
        last_order_date = parse_date(consumer.get("last_order_date"))

        consumer_data = {
            "id": consumer.get("id", ""),
            "store_id": store_id,
            "phone": consumer.get("phone"),
            "name": consumer.get("name"),
            "type": consumer.get("type"),
            "number_of_orders": consumer.get("number_of_orders"),
            "last_order_date": last_order_date,
            "preferences": consumer.get("preferences") or {},
            "raw_data": consumer,
        }
        consumer_records.append(consumer_data)

    if consumer_records:
        stmt = insert(Consumer).values(consumer_records)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "phone": stmt.excluded.phone,
                "name": stmt.excluded.name,
                "type": stmt.excluded.type,
                "number_of_orders": stmt.excluded.number_of_orders,
                "last_order_date": stmt.excluded.last_order_date,
                "preferences": stmt.excluded.preferences,
                "raw_data": stmt.excluded.raw_data,
            },
        )
        await session.execute(stmt)
        await session.commit()

    logger.info(f"Loaded {len(consumer_records)} consumers")
    return len(consumer_records)


async def load_consumer_preferences_data(
    session: AsyncSession,
    file_path: Path,
    store_id: str,
) -> int:
    """Load consumer preferences and merge into consumers."""
    logger.info(f"Loading consumer preferences data from {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        preferences = json.load(f)

    if not isinstance(preferences, list):
        logger.error("Consumer preferences data must be a list")
        return 0

    updated_count = 0

    for pref in preferences:
        consumer_id = pref.get("store_consumer_id")
        if not consumer_id:
            continue

        # Find consumer and update preferences
        stmt = select(Consumer).where(
            Consumer.id == consumer_id, Consumer.store_id == store_id
        )
        result = await session.execute(stmt)
        consumer = result.scalar_one_or_none()

        if consumer:
            # Merge preferences
            existing_prefs = consumer.preferences or {}
            new_prefs = pref.get("preferences", {})
            merged_prefs = {**existing_prefs, **new_prefs}

            consumer.preferences = merged_prefs
            # Also update raw_data
            consumer_raw_data = consumer.raw_data or {}
            consumer_raw_data["preferences_data"] = pref
            consumer.raw_data = consumer_raw_data

            updated_count += 1

    await session.commit()
    logger.info(f"Updated preferences for {updated_count} consumers")
    return updated_count


async def load_feedbacks_data(
    session: AsyncSession,
    file_path: Path,
    store_id: str,
) -> int:
    """Load feedbacks data from JSON file."""
    logger.info(f"Loading feedbacks data from {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        feedbacks = json.load(f)

    if not isinstance(feedbacks, list):
        logger.error("Feedbacks data must be a list")
        return 0

    feedback_records = []

    for feedback in feedbacks:
        created_at = parse_date(feedback.get("created_at"))

        feedback_data = {
            "id": feedback.get("id", ""),
            "store_id": store_id,
            "store_consumer_id": feedback.get("store_consumer_id"),
            "order_id": feedback.get("order_id"),
            "category": feedback.get("category"),
            "rating": feedback.get("rating"),
            "response": feedback.get("rated_response"),
            "created_at": created_at,
            "raw_data": feedback,
        }
        feedback_records.append(feedback_data)

    if feedback_records:
        stmt = insert(Feedback).values(feedback_records)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "store_consumer_id": stmt.excluded.store_consumer_id,
                "order_id": stmt.excluded.order_id,
                "category": stmt.excluded.category,
                "rating": stmt.excluded.rating,
                "response": stmt.excluded.response,
                "created_at": stmt.excluded.created_at,
                "raw_data": stmt.excluded.raw_data,
            },
        )
        await session.execute(stmt)
        await session.commit()

    logger.info(f"Loaded {len(feedback_records)} feedbacks")
    return len(feedback_records)


async def load_menu_events_data(
    session: AsyncSession,
    file_path: Path,
    store_id: str,
    batch_size: int = 5000,
) -> int:
    """Load menu events data from JSON file."""
    logger.info(f"Loading menu events data from {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        # File appears to be JSONL (one JSON object per line)
        events = []
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Error parsing JSON line: {e}")
                    continue

    if not events:
        logger.error("No menu events found")
        return 0

    total_loaded = 0

    for i in range(0, len(events), batch_size):
        batch = events[i : i + batch_size]
        event_records = []

        for event in batch:
            timestamp = parse_date(event.get("timestamp")) or parse_date(
                event.get("created_at")
            )

            # Parse metadata JSON string
            metadata_str = event.get("metadata", "{}")
            event_metadata = (
                parse_json_string(metadata_str)
                if isinstance(metadata_str, str)
                else metadata_str
            )

            event_data = {
                "id": event.get("id", ""),
                "store_id": store_id,
                "event_type": event.get("event_type", ""),
                "session_id": event.get("session_id"),
                "timestamp": timestamp,
                "device_type": event.get("device_type"),
                "platform": event.get("platform"),
                "event_metadata": event_metadata,
                "raw_data": event,  # Store complete original data
            }
            event_records.append(event_data)

        if event_records:
            stmt = insert(MenuEvent).values(event_records)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "event_type": stmt.excluded.event_type,
                    "session_id": stmt.excluded.session_id,
                    "timestamp": stmt.excluded.timestamp,
                    "device_type": stmt.excluded.device_type,
                    "platform": stmt.excluded.platform,
                    "event_metadata": stmt.excluded.event_metadata,
                    "raw_data": stmt.excluded.raw_data,
                },
            )
            await session.execute(stmt)
            await session.commit()

            total_loaded += len(event_records)
            logger.info(
                f"Loaded batch {i // batch_size + 1}: {len(event_records)} events (total: {total_loaded})"
            )

    logger.info(f"Loaded {total_loaded} menu events total")
    return total_loaded


async def load_all_data(
    session: AsyncSession,
    data_dir: Path,
    store_id: str,
    skip_chroma: bool = False,
) -> Dict[str, int]:
    """
    Load all data files from data directory.

    Args:
        session: Database session
        data_dir: Path to data directory
        store_id: Store ID
        skip_chroma: Skip Chroma document compilation

    Returns:
        Dictionary with counts per data type
    """
    results = {}

    # Load store data
    store_file = data_dir / "store.json"
    if store_file.exists():
        results["store"] = await load_store_data(session, store_file, store_id)
    else:
        logger.warning(f"Store file not found: {store_file}")
        results["store"] = 0

    # Load orders
    orders_file = data_dir / "orders.json"
    if orders_file.exists():
        results["orders"] = await load_orders_data(session, orders_file, store_id)
    else:
        logger.warning(f"Orders file not found: {orders_file}")
        results["orders"] = 0

    # Load campaigns
    campaigns_file = data_dir / "campaigns.json"
    if campaigns_file.exists():
        results["campaigns"] = await load_campaigns_data(
            session, campaigns_file, store_id
        )
    else:
        logger.warning(f"Campaigns file not found: {campaigns_file}")
        results["campaigns"] = 0

    # Load campaign results
    campaign_results_file = data_dir / "campaigns_results.json"
    if campaign_results_file.exists():
        results["campaign_results"] = await load_campaign_results_data(
            session, campaign_results_file, store_id
        )
    else:
        logger.warning(f"Campaign results file not found: {campaign_results_file}")
        results["campaign_results"] = 0

    # Load consumers
    consumers_file = data_dir / "store_consumers.json"
    if consumers_file.exists():
        results["consumers"] = await load_consumers_data(
            session, consumers_file, store_id
        )
    else:
        logger.warning(f"Consumers file not found: {consumers_file}")
        results["consumers"] = 0

    # Load consumer preferences
    preferences_file = data_dir / "store_consumer_preferences.json"
    if preferences_file.exists():
        results["consumer_preferences"] = await load_consumer_preferences_data(
            session, preferences_file, store_id
        )
    else:
        logger.warning(f"Consumer preferences file not found: {preferences_file}")
        results["consumer_preferences"] = 0

    # Load feedbacks
    feedbacks_file = data_dir / "feedbacks.json"
    if feedbacks_file.exists():
        results["feedbacks"] = await load_feedbacks_data(
            session, feedbacks_file, store_id
        )
    else:
        logger.warning(f"Feedbacks file not found: {feedbacks_file}")
        results["feedbacks"] = 0

    # Load menu events
    menu_events_file = data_dir / "menu_events_last_30_days.json"
    if menu_events_file.exists():
        results["menu_events"] = await load_menu_events_data(
            session, menu_events_file, store_id
        )
    else:
        logger.warning(f"Menu events file not found: {menu_events_file}")
        results["menu_events"] = 0

    return results


__all__ = [
    "load_store_data",
    "load_orders_data",
    "load_campaigns_data",
    "load_campaign_results_data",
    "load_consumers_data",
    "load_consumer_preferences_data",
    "load_feedbacks_data",
    "load_menu_events_data",
    "load_all_data",
]
