"""
Script to preload insights cache for all dashboard pages.
Run this periodically or after data updates to ensure fast insight loading.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.graphs.insights import generate_insight_for_page
from app.services.cache_service import get_cache_service

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def preload_insights(store_id: str):
    """
    Preload insights cache for all dashboard pages.

    Args:
        store_id: Store identifier
    """
    page_types = ["orders", "campaigns", "consumers", "feedbacks", "menu_events"]
    cache_service = get_cache_service()

    logger.info(f"Starting insights preload for store: {store_id}")
    logger.info("=" * 60)

    for page_type in page_types:
        try:
            logger.info(f"\n📊 Generating insight for {page_type}...")

            # Generate the insight
            insight_text = await generate_insight_for_page(
                store_id=store_id, page_type=page_type
            )

            # Cache it
            success = await cache_service.set_insight(
                store_id=store_id,
                page_type=page_type,
                insight=insight_text,
                ttl=300,  # 5 minutes
            )

            if success:
                logger.info(f"✓ Successfully cached insight for {page_type}")
                logger.info(f"  Preview: {insight_text[:100]}...")
            else:
                logger.error(f"✗ Failed to cache insight for {page_type}")

        except Exception as e:
            logger.error(
                f"✗ Error generating insight for {page_type}: {e}", exc_info=True
            )

    logger.info("\n" + "=" * 60)
    logger.info("✓ Insights preload complete!")
    logger.info("Insights are cached for 5 minutes and will be served instantly.")


async def main():
    """Main entry point."""
    # Get store ID from environment or use default
    import os
    from app.core.config import settings

    store_id = os.getenv(
        "STORE_ID",
        settings.STORE_ID if hasattr(settings, "STORE_ID") else "0WcZ1MWEaFc1VftEBdLa",
    )

    logger.info(f"Preloading insights for store: {store_id}")
    await preload_insights(store_id)


if __name__ == "__main__":
    asyncio.run(main())
