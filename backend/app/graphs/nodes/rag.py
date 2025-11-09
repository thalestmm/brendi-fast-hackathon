"""
RAG retrieval node for LangGraph agent.
"""

import logging
from typing import Dict, Any

from langchain_core.messages import HumanMessage

from app.services.rag_service import get_relevant_context

logger = logging.getLogger(__name__)


def retrieve_rag_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve relevant context from RAG before agent processes the message.
    
    Args:
        state: LangGraph state dictionary
    
    Returns:
        Updated state with retrieved context
    """
    try:
        store_id = state.get("store_id")
        messages = state.get("messages", [])
        
        if not store_id:
            logger.warning("No store_id in state, skipping RAG retrieval")
            return {"rag_context": ""}
        
        # Get the last user message
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
            elif hasattr(msg, "type") and msg.type == "human":
                user_message = msg.content
                break
            elif isinstance(msg, dict) and msg.get("role") == "user":
                user_message = msg.get("content")
                break
        
        if not user_message:
            logger.debug("No user message found, skipping RAG retrieval")
            return {"rag_context": ""}
        
        # Retrieve relevant context
        context = get_relevant_context(
            store_id=store_id,
            query=user_message,
            top_k=5,
        )
        
        logger.debug(f"Retrieved RAG context: {len(context)} characters")
        return {"rag_context": context}
    
    except Exception as e:
        logger.error(f"Error retrieving RAG context: {e}")
        return {"rag_context": f"Error retrieving context: {str(e)}"}


__all__ = ["retrieve_rag_context"]

