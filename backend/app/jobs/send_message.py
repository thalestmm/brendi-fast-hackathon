"""
Background job for processing buffered messages.
"""

import logging
import uuid
from datetime import datetime

from app.core.buffer import (
    get_buffered_messages,
    clear_buffer,
    combine_messages,
)
from app.core.database import AsyncSessionLocal
from app.models.chat import ChatMessage
from app.services.agent_service import process_message

logger = logging.getLogger(__name__)


async def process_buffered_messages(
    store_id: str,
    session_id: str,
) -> str:
    """
    Process buffered messages for a session.
    
    This function is called by the RQ worker after the buffer timeout.
    It combines all buffered messages and processes them as one.
    
    Args:
        store_id: Store identifier
        session_id: Chat session ID (string)
    
    Returns:
        Assistant response text
    """
    try:
        # Get buffered messages
        messages = await get_buffered_messages(store_id, session_id)
        
        if not messages:
            logger.warning(
                f"No buffered messages found for store_id={store_id}, "
                f"session_id={session_id}"
            )
            return "No messages to process."
        
        # Combine messages
        combined_message = await combine_messages(messages)
        
        if not combined_message.strip():
            logger.warning("Combined message is empty")
            await clear_buffer(store_id, session_id)
            return ""
        
        logger.info(
            f"Processing {len(messages)} buffered messages for "
            f"store_id={store_id}, session_id={session_id}"
        )
        
        # Parse session_id
        session_uuid = uuid.UUID(session_id)
        
        # Process with agent
        async with AsyncSessionLocal() as db:
            # Save user messages
            for msg in messages:
                user_msg = ChatMessage(
                    session_id=session_uuid,
                    store_id=store_id,
                    role="user",
                    content=msg["content"],
                    created_at=datetime.fromisoformat(msg["timestamp"]),
                )
                db.add(user_msg)
            await db.flush()
            
            # Process combined message with agent
            assistant_response = await process_message(
                session=db,
                session_id=session_uuid,
                store_id=store_id,
                user_message=combined_message,
            )
            
            # Save assistant message
            assistant_msg = ChatMessage(
                session_id=session_uuid,
                store_id=store_id,
                role="assistant",
                content=assistant_response,
                created_at=datetime.now(),
            )
            db.add(assistant_msg)
            await db.commit()
        
        # Clear buffer
        await clear_buffer(store_id, session_id)
        
        logger.info(
            f"Successfully processed buffered messages for "
            f"store_id={store_id}, session_id={session_id}"
        )
        
        # Notify WebSocket connections if active
        from app.routers.api.v1.websocket import manager
        try:
            await manager.send_message(store_id, session_id, {
                "type": "message",
                "role": "assistant",
                "content": assistant_response,
                "session_id": session_id,
            })
        except Exception as e:
            logger.debug(f"Could not send WebSocket notification: {e}")
        
        return assistant_response
    
    except Exception as e:
        logger.error(
            f"Error processing buffered messages: {e}",
            exc_info=True,
        )
        # Clear buffer on error to prevent stuck state
        await clear_buffer(store_id, session_id)
        raise


# Synchronous wrapper for RQ worker
def process_buffered_messages_sync(store_id: str, session_id: str) -> str:
    """
    Synchronous wrapper for RQ worker.
    
    This function is called by the RQ worker to process buffered messages.
    It creates a new event loop since RQ workers run in a synchronous context.
    
    Args:
        store_id: Store identifier
        session_id: Chat session ID (string)
    
    Returns:
        Assistant response text
    """
    import asyncio
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Create a new event loop for this worker thread
        # RQ workers run synchronously, so we need to create our own loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                process_buffered_messages(store_id, session_id)
            )
            return result
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(
            f"Error in process_buffered_messages_sync: {e}",
            exc_info=True,
        )
        raise


__all__ = ["process_buffered_messages", "process_buffered_messages_sync"]

