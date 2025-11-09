"""
RAG (Retrieval-Augmented Generation) service for querying vector database.
"""

import logging
from typing import List, Dict, Any, Optional

from app.services.chroma_service import query_collection, get_collection_count

logger = logging.getLogger(__name__)


def query_chroma(
    store_id: str,
    query_text: str,
    top_k: int = 5,
    content_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Query Chroma collection for relevant context.

    Args:
        store_id: Store identifier
        query_text: Query text
        top_k: Number of results to return
        content_types: Optional filter by content types (e.g., ['order', 'campaign'])

    Returns:
        Dictionary with query results
    """
    where_clause = None
    if content_types:
        where_clause = {"content_type": {"$in": content_types}}

    try:
        results = query_collection(
            store_id=store_id,
            query_text=query_text,
            top_k=top_k,
            where=where_clause,
        )
        return results
    except Exception as e:
        logger.error(f"Error querying Chroma for RAG: {e}")
        raise


def get_relevant_context(
    store_id: str,
    query: str,
    content_types: Optional[List[str]] = None,
    top_k: int = 5,
) -> str:
    """
    Get relevant context as formatted string for agent prompt.

    Args:
        store_id: Store identifier
        query: User query
        content_types: Optional filter by content types
        top_k: Number of results to return

    Returns:
        Formatted context string
    """
    try:
        results = query_chroma(
            store_id=store_id,
            query_text=query,
            top_k=top_k,
            content_types=content_types,
        )

        if not results or not results.get("documents") or not results["documents"][0]:
            return "No relevant context found."

        documents = results["documents"][0]
        metadatas = results.get("metadatas", [[]])[0]

        context_parts = []
        for i, doc in enumerate(documents):
            metadata = metadatas[i] if i < len(metadatas) else {}
            content_type = metadata.get("content_type", "unknown")
            context_parts.append(f"[{content_type.upper()}] {doc}")

        context = "\n\n".join(context_parts)
        logger.debug(f"Retrieved {len(documents)} context documents for query")
        return context

    except Exception as e:
        logger.error(f"Error getting relevant context: {e}")
        return f"Error retrieving context: {str(e)}"


def get_context_summary(store_id: str) -> Dict[str, Any]:
    """
    Get summary of available context in Chroma for a store.

    Args:
        store_id: Store identifier

    Returns:
        Dictionary with context summary
    """
    try:
        count = get_collection_count(store_id)
        return {
            "store_id": store_id,
            "document_count": count,
            "has_context": count > 0,
        }
    except Exception as e:
        logger.error(f"Error getting context summary: {e}")
        return {
            "store_id": store_id,
            "document_count": 0,
            "has_context": False,
            "error": str(e),
        }


__all__ = [
    "query_chroma",
    "get_relevant_context",
    "get_context_summary",
]
