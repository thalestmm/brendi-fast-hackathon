"""
Redis connection and RQ configuration utilities.
"""

import logging
from typing import Optional, Callable, Any

import redis
import redis.asyncio as aioredis
from rq import Queue

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis Connection Instances
_redis_sync_connection: Optional[redis.Redis] = None
_redis_async_connection: Optional[aioredis.AsyncRedis] = None


def get_redis_connection() -> redis.Redis:
    """
    Singleton pattern to get the sync Redis client.
    """
    global _redis_sync_connection

    if _redis_sync_connection is None:
        _redis_sync_connection = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=False,  # Binary data for RQ
            health_check_interval=30,  # 30 seconds
        )

    # Test connection
    try:
        _redis_sync_connection.ping()
        logger.info("Redis sync connection established")
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise

    return _redis_sync_connection


def get_async_redis_connection() -> aioredis.AsyncRedis:
    """
    Singleton pattern to get the async Redis client.
    """
    global _redis_async_connection

    if _redis_async_connection is None:
        _redis_async_connection = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,  # Decode responses to directly parse inside API
            health_check_interval=30,  # 30 seconds
        )

    # Test connection
    try:
        _redis_async_connection.ping()
        logger.info("Redis async connection established")
    except aioredis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise

    return _redis_async_connection


def get_queue(queue_name: Optional[str] = None) -> Queue:
    """
    Get an RQ queue instance.

    Args:
        queue_name: Name of the queue

    Returns:
        Queue: RQ Queue instance
    """
    if queue_name is None:
        queue_name = settings.RQ_QUEUE_NAME

    logger.debug(f"Getting queue: {queue_name}")

    redis_conn = get_redis_connection()
    return Queue(queue_name, connection=redis_conn)


def enqueue_job(
    func: Callable[..., Any], queue_name: Optional[str] = None, *args, **kwargs
):
    """
    Enqueue a job to an RQ queue.

    Args:
        func: Function to execute
        queue_name: Name of the queue
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function and job options

    Returns:
        Job: RQ Job instance
    """

    if queue_name is None:
        queue_name = settings.RQ_QUEUE_NAME

    queue = get_queue(queue_name)
    logger.debug(f"Enqueuing job: {func.__name__} to queue: {queue_name}")
    return queue.enqueue(func, *args, **kwargs)


# Alias functions for backward compatibility
get_redis_client = get_redis_connection
get_async_redis_client = get_async_redis_connection

__all__ = [
    "get_redis_connection",
    "get_async_redis_connection",
    "get_queue",
    "enqueue_job",
    "get_redis_client",
    "get_async_redis_client",
]
