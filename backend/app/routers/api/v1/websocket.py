"""
WebSocket endpoints for real-time chat.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from sqlalchemy import select

from app.models.chat import ChatSession, ChatMessage
from app.services.agent_service import process_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections per store and session."""
    
    def __init__(self):
        # {store_id: {session_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, store_id: str, session_id: str):
        """Accept a WebSocket connection."""
        await websocket.accept()
        
        if store_id not in self.active_connections:
            self.active_connections[store_id] = {}
        
        self.active_connections[store_id][session_id] = websocket
        logger.info(f"WebSocket connected: store_id={store_id}, session_id={session_id}")
    
    def disconnect(self, store_id: str, session_id: str):
        """Remove a WebSocket connection."""
        if store_id in self.active_connections:
            self.active_connections[store_id].pop(session_id, None)
            if not self.active_connections[store_id]:
                del self.active_connections[store_id]
        logger.info(f"WebSocket disconnected: store_id={store_id}, session_id={session_id}")
    
    async def send_message(self, store_id: str, session_id: str, message: Dict[str, Any]):
        """Send a message to a specific session."""
        if store_id in self.active_connections:
            websocket = self.active_connections[store_id].get(session_id)
            if websocket:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
                    self.disconnect(store_id, session_id)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/chat/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for real-time chat.
    
    Expected message format:
    {
        "type": "message",
        "content": "user message text",
        "store_id": "store-id-here"
    }
    
    Response format:
    {
        "type": "message" | "typing" | "error",
        "content": "response text",
        "role": "assistant" | "user",
        "session_id": "session-id"
    }
    """
    store_id = None
    session_uuid = None
    
    try:
        # Get store_id from query params or first message
        store_id_param = websocket.query_params.get("store_id")
        
        # Wait for first message to get store_id if not in query params
        first_message = await websocket.receive_json()
        
        if not store_id_param:
            store_id = first_message.get("store_id")
        else:
            store_id = store_id_param
        
        if not store_id:
            await websocket.send_json({
                "type": "error",
                "content": "store_id is required",
            })
            await websocket.close()
            return
        
        # Parse session_id
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            await websocket.send_json({
                "type": "error",
                "content": "Invalid session_id format",
            })
            await websocket.close()
            return
        
        # Get or create session
        from app.core.database import AsyncSessionLocal
        
        # Initialize session
        async with AsyncSessionLocal() as db:
            stmt = select(ChatSession).where(
                ChatSession.id == session_uuid,
                ChatSession.store_id == store_id
            )
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                # Create new session
                new_session = ChatSession(
                    id=session_uuid,
                    store_id=store_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    is_active=True,
                )
                db.add(new_session)
                await db.commit()
                logger.info(f"Created new chat session: {session_uuid}")
        
        # Connect WebSocket (outside of db session)
        await manager.connect(websocket, store_id, session_id)
        
        try:
            # Process the first message
            if first_message.get("type") == "message":
                await handle_chat_message(
                    store_id, session_uuid, first_message.get("content", "")
                )
            
            # Listen for more messages
            while True:
                data = await websocket.receive_json()
                
                if data.get("type") == "message":
                    content = data.get("content", "")
                    if content:
                        await handle_chat_message(store_id, session_uuid, content)
                else:
                    logger.warning(f"Unknown message type: {data.get('type')}")
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {store_id}/{session_id}")
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}", exc_info=True)
            if websocket.client_state.name == "CONNECTED":
                await websocket.send_json({
                    "type": "error",
                    "content": f"An error occurred: {str(e)}",
                })
        finally:
            manager.disconnect(store_id, session_id)
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}", exc_info=True)
        if websocket.client_state.name == "CONNECTED":
            await websocket.send_json({
                "type": "error",
                "content": f"Connection error: {str(e)}",
            })
            await websocket.close()


async def handle_chat_message(
    store_id: str, session_id: uuid.UUID, user_message: str
):
    """Handle a chat message with buffering and send response via WebSocket."""
    from app.core.buffer import add_message_to_buffer
    from app.core.redis import enqueue_job
    from app.jobs.send_message import process_buffered_messages_sync
    
    try:
        # Send typing indicator
        await manager.send_message(store_id, str(session_id), {
            "type": "typing",
            "content": "",
        })
        
        # Add message to buffer
        buffer_info = await add_message_to_buffer(
            store_id=store_id,
            session_id=str(session_id),
            message=user_message,
        )
        
        # Send user message confirmation
        await manager.send_message(store_id, str(session_id), {
            "type": "message",
            "role": "user",
            "content": user_message,
            "session_id": str(session_id),
        })
        
        # If this is the first message, schedule the job
        if buffer_info["is_first_message"]:
            from datetime import datetime as dt
            process_at = dt.fromisoformat(buffer_info["process_at"])
            delay_seconds = max(0, (process_at - dt.now()).total_seconds())
            
            # Enqueue job to process after buffer timeout
            enqueue_job(
                process_buffered_messages_sync,
                args=(store_id, str(session_id)),
                job_timeout=300,  # 5 minutes timeout
            )
            
            logger.info(
                f"Scheduled buffered message processing via WebSocket for "
                f"store_id={store_id}, session_id={session_id}, "
                f"delay={delay_seconds}s"
            )
            
            # Note: The actual response will be sent when the job completes
            # For now, we keep the typing indicator active
            # In a production system, you'd want to poll or use a pub/sub system
            # to notify the WebSocket when the job completes
        
    except Exception as e:
        logger.error(f"Error handling chat message: {e}", exc_info=True)
        await manager.send_message(store_id, str(session_id), {
            "type": "error",
            "content": f"Error processing message: {str(e)}",
        })


__all__ = ["router", "manager"]

