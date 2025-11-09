"""
Chat API endpoints.
"""

import logging
from datetime import datetime
from typing import List
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func

from app.core.dependencies import DbSession, StoreId
from app.models.chat import ChatSession, ChatMessage
from app.schemas.api.v1.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionsResponse,
    ChatMessage as ChatMessageSchema,
    ChatSession as ChatSessionSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    store_id: StoreId,
    db: DbSession,
    request: ChatMessageRequest,
) -> ChatMessageResponse:
    """
    Send a message to the AI agent.

    TODO: Integrate with LangGraph agent to process messages.
    For now, returns a placeholder response.
    """
    # Get or create session
    session_id = request.session_id
    if not session_id:
        # Create new session
        new_session = ChatSession(
            store_id=store_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True,
        )
        db.add(new_session)
        await db.flush()
        session_id = new_session.id
    else:
        # Verify session exists and belongs to store
        stmt = select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.store_id == store_id
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
            )

    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        store_id=store_id,
        role="user",
        content=request.message,
        created_at=datetime.now(),
    )
    db.add(user_message)
    await db.flush()

    # TODO: Process message with LangGraph agent
    # For now, return placeholder response
    assistant_response = "I'm here to help! This is a placeholder response. Chat functionality will be fully implemented soon."

    # Save assistant message
    assistant_message = ChatMessage(
        session_id=session_id,
        store_id=store_id,
        role="assistant",
        content=assistant_response,
        created_at=datetime.now(),
    )
    db.add(assistant_message)
    await db.commit()

    return ChatMessageResponse(
        message=ChatMessageSchema(
            id=assistant_message.id,
            role=assistant_message.role,
            content=assistant_message.content,
            created_at=assistant_message.created_at,
        ),
        session_id=session_id,
    )


@router.get("/sessions", response_model=ChatSessionsResponse)
async def get_sessions(
    store_id: StoreId,
    db: DbSession,
    limit: int = 20,
    offset: int = 0,
) -> ChatSessionsResponse:
    """Get chat sessions for a store."""
    # Get sessions
    stmt = (
        select(ChatSession)
        .where(ChatSession.store_id == store_id)
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)
    sessions = result.scalars().all()

    # Get message counts
    session_schemas = []
    for session in sessions:
        count_stmt = select(func.count(ChatMessage.id)).where(
            ChatMessage.session_id == session.id
        )
        count_result = await db.execute(count_stmt)
        message_count = count_result.scalar() or 0

        session_schemas.append(
            ChatSessionSchema(
                id=session.id,
                store_id=session.store_id,
                created_at=session.created_at,
                updated_at=session.updated_at,
                is_active=session.is_active,
                message_count=message_count,
            )
        )

    # Get total count
    total_stmt = select(func.count(ChatSession.id)).where(
        ChatSession.store_id == store_id
    )
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0

    return ChatSessionsResponse(
        sessions=session_schemas,
        total=total,
    )
