"""
Chroma service for vector database operations.
"""

import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings

from app.core.config import settings as app_settings

logger = logging.getLogger(__name__)

# Initialize Chroma client
_chroma_client: Optional[chromadb.ClientAPI] = None


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or create Chroma client singleton."""
    global _chroma_client

    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(
            host=app_settings.CHROMA_HOST or "localhost",
            port=app_settings.CHROMA_PORT or 8000,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        logger.info(
            f"Connected to Chroma at {app_settings.CHROMA_HOST}:{app_settings.CHROMA_PORT}"
        )

    return _chroma_client


def get_collection_name(store_id: str) -> str:
    """Get collection name for a store."""
    return f"store_{store_id}"


def get_or_create_collection(store_id: str) -> chromadb.Collection:
    """
    Get or create a Chroma collection for a store.

    Args:
        store_id: Store identifier

    Returns:
        Chroma collection instance
    """
    client = get_chroma_client()
    collection_name = get_collection_name(store_id)

    try:
        collection = client.get_collection(name=collection_name)
        logger.debug(f"Retrieved existing collection: {collection_name}")
    except Exception:
        collection = client.create_collection(
            name=collection_name, metadata={"store_id": store_id}
        )
        logger.info(f"Created new collection: {collection_name}")

    return collection


def add_documents(
    store_id: str,
    documents: List[str],
    embeddings: Optional[List[List[float]]] = None,
    metadatas: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None,
) -> None:
    """
    Add documents to a store's Chroma collection.

    Args:
        store_id: Store identifier
        documents: List of document texts
        embeddings: Optional pre-computed embeddings
        metadatas: Optional metadata for each document
        ids: Optional IDs for each document
    """
    collection = get_or_create_collection(store_id)

    # Generate IDs if not provided
    if ids is None:
        ids = [f"doc_{i}" for i in range(len(documents))]

    # Ensure metadatas list matches documents
    if metadatas is None:
        metadatas = [{"store_id": store_id} for _ in documents]
    else:
        for metadata in metadatas:
            metadata["store_id"] = store_id

    try:
        if embeddings:
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )
        else:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
        logger.info(f"Added {len(documents)} documents to collection store_{store_id}")
    except Exception as e:
        logger.error(f"Error adding documents to Chroma: {e}")
        raise


def query_collection(
    store_id: str,
    query_text: str,
    top_k: int = 5,
    query_embeddings: Optional[List[List[float]]] = None,
    where: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Query a store's Chroma collection.

    Args:
        store_id: Store identifier
        query_text: Query text (if query_embeddings not provided)
        top_k: Number of results to return
        query_embeddings: Optional pre-computed query embeddings
        where: Optional metadata filter

    Returns:
        Dictionary with 'ids', 'documents', 'metadatas', 'distances'
    """
    collection = get_or_create_collection(store_id)

    # Build where clause to ensure store_id filtering
    if where is None:
        where = {"store_id": store_id}
    else:
        where["store_id"] = store_id

    try:
        if query_embeddings:
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=top_k,
                where=where,
            )
        else:
            results = collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=where,
            )

        logger.debug(f"Query returned {len(results.get('ids', [{}])[0])} results")
        return results
    except Exception as e:
        logger.error(f"Error querying Chroma: {e}")
        raise


def delete_collection(store_id: str) -> None:
    """
    Delete a store's Chroma collection.

    Args:
        store_id: Store identifier
    """
    client = get_chroma_client()
    collection_name = get_collection_name(store_id)

    try:
        client.delete_collection(name=collection_name)
        logger.info(f"Deleted collection: {collection_name}")
    except Exception as e:
        logger.warning(f"Error deleting collection {collection_name}: {e}")


def get_collection_count(store_id: str) -> int:
    """
    Get the number of documents in a store's collection.

    Args:
        store_id: Store identifier

    Returns:
        Number of documents
    """
    try:
        collection = get_or_create_collection(store_id)
        return collection.count()
    except Exception as e:
        logger.error(f"Error getting collection count: {e}")
        return 0


__all__ = [
    "get_chroma_client",
    "get_or_create_collection",
    "add_documents",
    "query_collection",
    "delete_collection",
    "get_collection_count",
]
