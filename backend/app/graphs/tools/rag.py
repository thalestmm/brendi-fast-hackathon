"""
RAG tool for querying vector database.
"""

import logging
from typing import Dict, Any, Optional, List

from langchain_core.tools import tool

from app.services.rag_service import get_relevant_context

logger = logging.getLogger(__name__)


@tool
def search_historical_data(
    store_id: str = "",
    query: str = "",
    content_types: Optional[List[str]] = None,
    top_k: int = 5,
) -> str:
    """
    Search historical restaurant data using semantic search (RAG).

    This tool searches through orders, campaigns, customer feedback, menu events,
    and other restaurant data to find relevant context for answering questions.

    Note: store_id is automatically provided - you don't need to specify it.

    Args:
        query: Search query/question
        content_types: Optional list of content types to filter by
                      (e.g., ['order', 'campaign', 'feedback'])
        top_k: Number of results to return (default: 5)

    Returns:
        Formatted context string with relevant information
    """
    try:
        context = get_relevant_context(
            store_id=store_id,
            query=query,
            content_types=content_types,
            top_k=top_k,
        )
        return context
    except Exception as e:
        logger.error(f"Error searching historical data: {e}")
        return f"Error retrieving context: {str(e)}"


__all__ = ["search_historical_data"]
