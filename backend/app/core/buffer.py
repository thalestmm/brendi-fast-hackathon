"""
Message buffering system for handling rapid consecutive messages.
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.core.redis import get_async_redis_connection
from app.core.config import settings

logger = logging.getLogger(__name__)

BUFFER_KEY_PREFIX = "message_buffer:"
PROCESS_AT_KEY_PREFIX = "message_buffer_process_at:"


async def add_message_to_buffer(
    store_id: str,
    session_id: str,
    message: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Add a message to the buffer queue.

    If this is the first message, sets a process_datetime.
    If messages already exist, appends to the queue and resets the timer.

    Args:
        store_id: Store identifier
        session_id: Chat session ID
        message: User message content
        user_id: Optional user identifier

    Returns:
        Dictionary with buffer status and process time
    """
    redis = await get_async_redis_connection()

    buffer_key = f"{BUFFER_KEY_PREFIX}{store_id}:{session_id}"
    process_at_key = f"{PROCESS_AT_KEY_PREFIX}{store_id}:{session_id}"

    try:
        # Get existing buffer
        existing_buffer = await redis.get(buffer_key)
        messages = json.loads(existing_buffer) if existing_buffer else []

        # Add new message
        message_entry = {
            "id": str(uuid.uuid4()),
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
        }
        messages.append(message_entry)

        # Calculate process time (now + timeout)
        process_at = datetime.now() + timedelta(
            seconds=settings.MESSAGE_BUFFER_TIMEOUT_SECONDS
        )
        process_at_iso = process_at.isoformat()

        # Store buffer and process time
        await redis.set(
            buffer_key,
            json.dumps(messages),
            ex=settings.MESSAGE_BUFFER_TIMEOUT_SECONDS
            + 10,  # Expire slightly after process time
        )
        await redis.set(
            process_at_key,
            process_at_iso,
            ex=settings.MESSAGE_BUFFER_TIMEOUT_SECONDS + 10,
        )

        is_first_message = len(messages) == 1

        logger.debug(
            f"Added message to buffer: store_id={store_id}, "
            f"session_id={session_id}, total_messages={len(messages)}, "
            f"process_at={process_at_iso}"
        )

        return {
            "buffer_key": buffer_key,
            "messages": messages,
            "process_at": process_at_iso,
            "is_first_message": is_first_message,
            "message_count": len(messages),
        }

    except Exception as e:
        logger.error(f"Error adding message to buffer: {e}", exc_info=True)
        raise


async def get_buffered_messages(
    store_id: str, session_id: str
) -> Optional[List[Dict[str, Any]]]:
    """
    Get buffered messages for a session.

    Args:
        store_id: Store identifier
        session_id: Chat session ID

    Returns:
        List of messages or None if buffer doesn't exist
    """
    redis = await get_async_redis_connection()
    buffer_key = f"{BUFFER_KEY_PREFIX}{store_id}:{session_id}"

    try:
        buffer_data = await redis.get(buffer_key)
        if buffer_data:
            return json.loads(buffer_data)
        return None
    except Exception as e:
        logger.error(f"Error getting buffered messages: {e}")
        return None


async def clear_buffer(store_id: str, session_id: str) -> bool:
    """
    Clear the message buffer for a session.

    Args:
        store_id: Store identifier
        session_id: Chat session ID

    Returns:
        True if buffer was cleared, False if it didn't exist
    """
    redis = await get_async_redis_connection()
    buffer_key = f"{BUFFER_KEY_PREFIX}{store_id}:{session_id}"
    process_at_key = f"{PROCESS_AT_KEY_PREFIX}{store_id}:{session_id}"

    try:
        deleted = await redis.delete(buffer_key, process_at_key)
        return deleted > 0
    except Exception as e:
        logger.error(f"Error clearing buffer: {e}")
        return False


async def combine_messages(messages: List[Dict[str, Any]]) -> str:
    """
    Combine multiple buffered messages into a single message.

    Args:
        messages: List of message dictionaries

    Returns:
        Combined message text
    """
    if not messages:
        return ""

    if len(messages) == 1:
        return messages[0]["content"]

    # Combine messages with separators
    combined_parts = []
    for msg in messages:
        content = msg["content"].strip()
        if content:
            combined_parts.append(content)

    return "\n\n".join(combined_parts)


async def get_pending_buffers() -> List[Dict[str, Any]]:
    """
    Get all buffers that are ready to be processed.

    Returns:
        List of buffer info dictionaries
    """
    redis = await get_async_redis_connection()
    now = datetime.now()
    ready_buffers = []

    try:
        # Get all process_at keys
        pattern = f"{PROCESS_AT_KEY_PREFIX}*"
        cursor = 0

        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)

            for key in keys:
                process_at_str = await redis.get(key)
                if process_at_str:
                    try:
                        process_at = datetime.fromisoformat(process_at_str)
                        if process_at <= now:
                            # Extract store_id and session_id from key
                            # Format: message_buffer_process_at:store_id:session_id
                            parts = key.replace(PROCESS_AT_KEY_PREFIX, "").split(":", 1)
                            if len(parts) == 2:
                                store_id, session_id = parts

                                # Get messages
                                messages = await get_buffered_messages(
                                    store_id, session_id
                                )

                                if messages:
                                    ready_buffers.append(
                                        {
                                            "store_id": store_id,
                                            "session_id": session_id,
                                            "messages": messages,
                                            "process_at": process_at_str,
                                        }
                                    )
                    except Exception as e:
                        logger.error(f"Error processing buffer key {key}: {e}")
                        continue

            if cursor == 0:
                break

        return ready_buffers

    except Exception as e:
        logger.error(f"Error getting pending buffers: {e}", exc_info=True)
        return []


__all__ = [
    "add_message_to_buffer",
    "get_buffered_messages",
    "clear_buffer",
    "combine_messages",
    "get_pending_buffers",
]
