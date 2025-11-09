"""
Service for interacting with the LangGraph agent.
"""

import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage as LangChainBaseMessage

from app.graphs.agent import graph
from app.core.config import settings
from langgraph.graph import add_messages
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# Define AgentState locally to avoid circular imports
class AgentState(TypedDict):
    """State for the LangGraph agent."""

    messages: Annotated[List[LangChainBaseMessage], add_messages]
    store_id: str
    rag_context: str


# Number of recent messages to include in context
MESSAGE_HISTORY_LIMIT = settings.AGENT_MESSAGE_HISTORY_LIMIT


async def get_recent_messages(
    session: AsyncSession, session_id: uuid.UUID, limit: int = MESSAGE_HISTORY_LIMIT
) -> List[BaseMessage]:
    """
    Get recent messages from database and convert to LangChain messages.

    Args:
        session: Database session
        session_id: Chat session ID
        limit: Maximum number of messages to retrieve

    Returns:
        List of LangChain messages
    """
    from app.models.chat import ChatMessage

    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    db_messages = result.scalars().all()

    # Convert to LangChain messages (reverse to get chronological order)
    messages = []
    for db_msg in reversed(db_messages):
        if db_msg.role == "user":
            messages.append(HumanMessage(content=db_msg.content))
        elif db_msg.role == "assistant":
            messages.append(AIMessage(content=db_msg.content))

    return messages


async def process_message(
    session: AsyncSession,
    session_id: uuid.UUID,
    store_id: str,
    user_message: str,
) -> str:
    """
    Process a user message through the LangGraph agent.

    Args:
        session: Database session
        session_id: Chat session ID
        store_id: Store identifier
        user_message: User's message text

    Returns:
        Assistant's response text
    """
    try:
        # Get recent message history
        messages = await get_recent_messages(session, session_id)

        # Add new user message
        new_user_message = HumanMessage(content=user_message)
        messages.append(new_user_message)

        # Prepare state (no checkpointing - we manage history in DB)
        initial_state: AgentState = {
            "messages": messages,
            "store_id": store_id,
            "rag_context": "",
        }

        # Invoke the graph without checkpointing
        logger.info(f"Invoking agent graph for session {session_id}")
        
        # Collect all messages from the graph execution
        all_messages = []
        async for event in graph.astream(initial_state):
            for node_name, node_output in event.items():
                logger.debug(
                    f"Node {node_name} output: {type(node_output)}"
                )
                # Collect messages from each node
                if isinstance(node_output, dict) and "messages" in node_output:
                    all_messages.extend(node_output["messages"])

        # Extract the final AI response
        for msg in reversed(all_messages):
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content

        # Fallback if no response found
        return "I apologize, but I couldn't generate a response. Please try again."

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return f"I encountered an error: {str(e)}. Please try again."


__all__ = ["process_message", "get_recent_messages"]
