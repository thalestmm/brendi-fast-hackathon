"""
Service for interacting with the LangGraph agent.
"""

import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import TypedDict, Annotated, List as TypedList
from langchain_core.messages import BaseMessage as LangChainBaseMessage

from app.graphs.agent import graph
from app.core.config import settings
from app.models.chat import ChatSessionState
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# Define AgentState locally to avoid circular imports
class AgentState(TypedDict):
    """State for the LangGraph agent."""

    messages: Annotated[TypedList[LangChainBaseMessage], "Chat messages"]
    store_id: str
    rag_context: str


# Number of recent messages to include in context
MESSAGE_HISTORY_LIMIT = settings.AGENT_MESSAGE_HISTORY_LIMIT


async def get_or_create_state(
    session: AsyncSession, session_id: uuid.UUID, store_id: str
) -> str:
    """
    Get or create LangGraph checkpoint state for a session.

    Returns:
        Checkpoint thread ID for LangGraph
    """
    stmt = select(ChatSessionState).where(ChatSessionState.session_id == session_id)
    result = await session.execute(stmt)
    state_record = result.scalar_one_or_none()

    if state_record:
        return str(state_record.id)

    # Create new state record
    new_state = ChatSessionState(
        session_id=session_id,
        store_id=store_id,
        state={},
        updated_at=datetime.now(),
    )
    session.add(new_state)
    await session.flush()

    return str(new_state.id)


async def save_state(
    session: AsyncSession,
    thread_id: str,
    session_id: uuid.UUID,
    state: Dict[str, Any],
) -> None:
    """Save LangGraph state to database."""
    try:
        stmt = select(ChatSessionState).where(
            ChatSessionState.id == uuid.UUID(thread_id)
        )
        result = await session.execute(stmt)
        state_record = result.scalar_one_or_none()

        if state_record:
            state_record.state = state
            state_record.updated_at = datetime.now()
            await session.commit()
    except Exception as e:
        logger.error(f"Error saving state: {e}")
        await session.rollback()


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
        # Get or create checkpoint thread
        thread_id = await get_or_create_state(session, session_id, store_id)

        # Get recent message history
        messages = await get_recent_messages(session, session_id)

        # Add new user message
        new_user_message = HumanMessage(content=user_message)
        messages.append(new_user_message)

        # Prepare state and config
        # Include store_id in config for tool injection
        config = {
            "configurable": {
                "thread_id": thread_id,
                "store_id": store_id,  # Available for tool injection
            }
        }
        initial_state: AgentState = {
            "messages": messages,
            "store_id": store_id,
            "rag_context": "",
        }

        # Invoke the graph
        logger.info(f"Invoking agent graph for session {session_id}")
        final_state = None

        # Stream through the graph
        async for event in graph.astream(initial_state, config):
            # Process events (tool calls, agent responses, etc.)
            for node_name, node_output in event.items():
                logger.debug(
                    f"Node {node_name} output keys: {list(node_output.keys()) if isinstance(node_output, dict) else type(node_output)}"
                )
                # Collect final state from agent node
                if node_name == "agent" and isinstance(node_output, dict):
                    if "messages" in node_output:
                        final_state = node_output

        # Extract the final response from the last state
        if final_state and "messages" in final_state:
            final_messages = final_state["messages"]
            # Get the last AI message
            for msg in reversed(final_messages):
                if isinstance(msg, AIMessage):
                    return msg.content

        # If no final state, try to get the last message from the graph state
        # Get the final state from checkpoint
        try:
            final_checkpoint = await graph.aget_state(config)
            if final_checkpoint and final_checkpoint.values:
                final_messages = final_checkpoint.values.get("messages", [])
                for msg in reversed(final_messages):
                    if isinstance(msg, AIMessage):
                        return msg.content
        except Exception as checkpoint_error:
            logger.warning(
                f"Could not retrieve final state from checkpoint: {checkpoint_error}"
            )

        # Fallback if no response found
        return "I apologize, but I couldn't generate a response. Please try again."

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return f"I encountered an error: {str(e)}. Please try again."


__all__ = ["process_message", "get_recent_messages"]
