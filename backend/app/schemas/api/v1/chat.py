"""
Chat API schemas.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class ChatMessageRequest(BaseModel):
    """Request to send a chat message."""

    message: str = Field(..., description="User message")
    session_id: Optional[uuid.UUID] = Field(
        None, description="Existing session ID (optional)"
    )


class ChatMessage(BaseModel):
    """Chat message model."""

    id: uuid.UUID
    role: str  # 'user' or 'assistant'
    content: str
    created_at: datetime


class ChatMessageResponse(BaseModel):
    """Response from chat message."""

    message: ChatMessage
    session_id: uuid.UUID


class ChatSession(BaseModel):
    """Chat session model."""

    id: uuid.UUID
    store_id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: Optional[int] = 0


class ChatSessionsResponse(BaseModel):
    """List of chat sessions."""

    sessions: List[ChatSession]
    total: int
