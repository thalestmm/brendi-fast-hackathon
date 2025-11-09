"""
Cache service for storing and retrieving cached data with TTL support.
"""

import json
import logging
from typing import Optional, Any, Dict
from datetime import datetime

from app.core.redis import get_async_redis_connection

logger = logging.getLogger(__name__)

# Cache key prefixes
INSIGHTS_CACHE_PREFIX = "insights"
ANALYTICS_CACHE_PREFIX = "analytics"

# Default TTL in seconds
DEFAULT_INSIGHTS_TTL = 300  # 5 minutes
DEFAULT_ANALYTICS_TTL = 60  # 1 minute


class CacheService:
    """Service for managing cached data in Redis."""

    def __init__(self):
        """Initialize the cache service with Redis connection."""
        self.redis = get_async_redis_connection()
        logger.debug("CacheService initialized")

    async def get_insight(
        self, store_id: str, page_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached insight for a specific store and page type.

        Args:
            store_id: Store identifier
            page_type: Type of page (orders, campaigns, etc.)

        Returns:
            Cached insight data or None if not found/expired
        """
        key = f"{INSIGHTS_CACHE_PREFIX}:{store_id}:{page_type}"
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                logger.info(f"✓ Cache hit for insight: {key}")
                return json.loads(cached_data)
            logger.info(f"✗ Cache miss for insight: {key}")
            return None
        except Exception as e:
            logger.error(
                f"Error retrieving cached insight for {key}: {e}", exc_info=True
            )
            return None

    async def set_insight(
        self,
        store_id: str,
        page_type: str,
        insight: str,
        ttl: int = DEFAULT_INSIGHTS_TTL,
    ) -> bool:
        """
        Cache an insight with TTL.

        Args:
            store_id: Store identifier
            page_type: Type of page
            insight: The insight text to cache
            ttl: Time to live in seconds

        Returns:
            True if successfully cached, False otherwise
        """
        key = f"{INSIGHTS_CACHE_PREFIX}:{store_id}:{page_type}"
        data = {
            "insight": insight,
            "page_type": page_type,
            "generated_at": datetime.now().isoformat(),
            "cached_at": datetime.now().isoformat(),
        }
        try:
            await self.redis.setex(key, ttl, json.dumps(data))
            logger.info(f"✓ Cached insight for {key} with TTL {ttl}s")
            return True
        except Exception as e:
            logger.error(f"✗ Error caching insight for {key}: {e}", exc_info=True)
            return False

    async def delete_insight(self, store_id: str, page_type: str) -> bool:
        """
        Delete a cached insight.

        Args:
            store_id: Store identifier
            page_type: Type of page

        Returns:
            True if deleted, False otherwise
        """
        key = f"{INSIGHTS_CACHE_PREFIX}:{store_id}:{page_type}"
        try:
            result = await self.redis.delete(key)
            logger.debug(f"Deleted cached insight: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error deleting cached insight: {e}")
            return False

    async def clear_store_insights(self, store_id: str) -> int:
        """
        Clear all cached insights for a store.

        Args:
            store_id: Store identifier

        Returns:
            Number of keys deleted
        """
        pattern = f"{INSIGHTS_CACHE_PREFIX}:{store_id}:*"
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Cleared {deleted} cached insights for store {store_id}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Error clearing store insights: {e}")
            return 0

    async def get_analytics(
        self, store_id: str, analytics_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached analytics data.

        Args:
            store_id: Store identifier
            analytics_type: Type of analytics (orders, campaigns, etc.)

        Returns:
            Cached analytics data or None if not found/expired
        """
        key = f"{ANALYTICS_CACHE_PREFIX}:{store_id}:{analytics_type}"
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                logger.debug(f"Cache hit for analytics: {key}")
                return json.loads(cached_data)
            logger.debug(f"Cache miss for analytics: {key}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached analytics: {e}")
            return None

    async def set_analytics(
        self,
        store_id: str,
        analytics_type: str,
        data: Dict[str, Any],
        ttl: int = DEFAULT_ANALYTICS_TTL,
    ) -> bool:
        """
        Cache analytics data with TTL.

        Args:
            store_id: Store identifier
            analytics_type: Type of analytics
            data: Analytics data to cache
            ttl: Time to live in seconds

        Returns:
            True if successfully cached, False otherwise
        """
        key = f"{ANALYTICS_CACHE_PREFIX}:{store_id}:{analytics_type}"
        cache_data = {
            **data,
            "_cached_at": datetime.now().isoformat(),
        }
        try:
            await self.redis.setex(key, ttl, json.dumps(cache_data))
            logger.debug(f"Cached analytics for {key} with TTL {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Error caching analytics: {e}")
            return False


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create the cache service singleton."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


__all__ = ["CacheService", "get_cache_service", "DEFAULT_INSIGHTS_TTL"]
