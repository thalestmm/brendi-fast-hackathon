"""
Health check script to verify all system components are working correctly.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def check_redis():
    """Check Redis connection."""
    logger.info("\n🔍 Checking Redis connection...")
    try:
        from app.core.redis import get_async_redis_connection

        redis_client = get_async_redis_connection()
        result = await redis_client.ping()

        if result:
            logger.info("  ✓ Redis is connected and responding")

            # Check Redis info
            info = await redis_client.info("server")
            redis_version = info.get("redis_version", "unknown")
            logger.info(f"  ✓ Redis version: {redis_version}")

            return True
        else:
            logger.error("  ✗ Redis ping failed")
            return False

    except Exception as e:
        logger.error(f"  ✗ Redis connection failed: {e}")
        logger.error(
            "  → Make sure Redis is running (docker-compose up redis or redis-server)"
        )
        return False


async def check_database():
    """Check database connection."""
    logger.info("\n🔍 Checking database connection...")
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()

        logger.info("  ✓ Database is connected and responding")
        return True

    except Exception as e:
        logger.error(f"  ✗ Database connection failed: {e}")
        logger.error("  → Check your DATABASE_URL environment variable")
        return False


async def check_cache_service():
    """Check cache service functionality."""
    logger.info("\n🔍 Checking cache service...")
    try:
        from app.services.cache_service import get_cache_service

        cache_service = get_cache_service()
        test_key = "health_check_test"
        test_value = "test_value"

        # Test set
        success = await cache_service.set_insight(
            store_id="test_store", page_type=test_key, insight=test_value, ttl=60
        )

        if not success:
            logger.error("  ✗ Failed to set cache value")
            return False

        # Test get
        cached_data = await cache_service.get_insight(
            store_id="test_store", page_type=test_key
        )

        if cached_data and cached_data.get("insight") == test_value:
            logger.info("  ✓ Cache service is working correctly")

            # Cleanup
            await cache_service.delete_insight("test_store", test_key)
            return True
        else:
            logger.error("  ✗ Cache service is not returning correct values")
            return False

    except Exception as e:
        logger.error(f"  ✗ Cache service check failed: {e}")
        return False


async def check_openai():
    """Check OpenAI API key."""
    logger.info("\n🔍 Checking OpenAI configuration...")
    try:
        from app.core.config import settings

        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key":
            logger.info("  ✓ OpenAI API key is configured")
            return True
        else:
            logger.warning("  ⚠ OpenAI API key is not set or using default value")
            logger.warning(
                "  → Set OPENAI_API_KEY environment variable for insights generation"
            )
            return False

    except Exception as e:
        logger.error(f"  ✗ Failed to check OpenAI configuration: {e}")
        return False


async def check_chroma():
    """Check ChromaDB connection."""
    logger.info("\n🔍 Checking ChromaDB connection...")
    try:
        from app.services.chroma_service import get_chroma_client

        client = get_chroma_client()
        heartbeat = client.heartbeat()

        if heartbeat:
            logger.info("  ✓ ChromaDB is connected and responding")
            return True
        else:
            logger.error("  ✗ ChromaDB heartbeat failed")
            return False

    except Exception as e:
        logger.error(f"  ✗ ChromaDB connection failed: {e}")
        logger.error("  → Make sure ChromaDB is running (docker-compose up chroma)")
        return False


async def check_insights_cache(store_id: str = "0WcZ1MWEaFc1VftEBdLa"):
    """Check if insights are cached for the default store."""
    logger.info(f"\n🔍 Checking cached insights for store {store_id}...")
    try:
        from app.services.cache_service import get_cache_service

        cache_service = get_cache_service()
        page_types = ["orders", "campaigns", "consumers"]
        cached_count = 0

        for page_type in page_types:
            cached_data = await cache_service.get_insight(store_id, page_type)
            if cached_data:
                cached_count += 1
                logger.info(f"  ✓ Insight cached for {page_type}")
            else:
                logger.info(f"  ✗ No cached insight for {page_type}")

        if cached_count > 0:
            logger.info(f"  ✓ Found {cached_count}/{len(page_types)} cached insights")
        else:
            logger.warning("  ⚠ No cached insights found")
            logger.warning(
                "  → Run 'python preload_insights.py' to preload insights cache"
            )

        return True

    except Exception as e:
        logger.error(f"  ✗ Failed to check cached insights: {e}")
        return False


async def main():
    """Run all health checks."""
    logger.info("=" * 70)
    logger.info("🏥 SYSTEM HEALTH CHECK")
    logger.info("=" * 70)

    results = {}

    # Run all checks
    results["redis"] = await check_redis()
    results["database"] = await check_database()
    results["cache"] = await check_cache_service()
    results["openai"] = await check_openai()
    results["chroma"] = await check_chroma()
    results["insights"] = await check_insights_cache()

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 HEALTH CHECK SUMMARY")
    logger.info("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for component, status in results.items():
        icon = "✓" if status else "✗"
        logger.info(f"  {icon} {component.upper()}: {'PASS' if status else 'FAIL'}")

    logger.info("\n" + "=" * 70)
    if passed == total:
        logger.info(f"✓ ALL CHECKS PASSED ({passed}/{total})")
        logger.info("=" * 70)
        return 0
    else:
        logger.warning(f"⚠ SOME CHECKS FAILED ({passed}/{total} passed)")
        logger.info("=" * 70)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
