"""
Embedding generation service using OpenAI API.
"""

import logging
from typing import List, Optional

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# OpenAI client singleton
_openai_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    """Get or create OpenAI client singleton."""
    global _openai_client

    if _openai_client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("Initialized OpenAI client")

    return _openai_client


def generate_embeddings_batch(
    texts: List[str],
    model: str = "text-embedding-3-small",
    batch_size: int = 100,
) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts.

    Args:
        texts: List of texts to embed
        model: OpenAI embedding model to use
        batch_size: Number of texts to process per API call

    Returns:
        List of embedding vectors
    """
    if not texts:
        return []

    client = get_openai_client()
    all_embeddings = []

    # Process in batches to avoid rate limits
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        try:
            response = client.embeddings.create(
                model=model,
                input=batch,
            )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

            logger.debug(
                f"Generated embeddings for batch {i // batch_size + 1} ({len(batch)} texts)"
            )

        except Exception as e:
            logger.error(f"Error generating embeddings for batch: {e}")
            # Retry logic could be added here
            raise

    logger.info(f"Generated {len(all_embeddings)} embeddings total")
    return all_embeddings


def generate_embedding_single(
    text: str, model: str = "text-embedding-3-small"
) -> List[float]:
    """
    Generate embedding for a single text.

    Args:
        text: Text to embed
        model: OpenAI embedding model to use

    Returns:
        Embedding vector
    """
    embeddings = generate_embeddings_batch([text], model=model, batch_size=1)
    return embeddings[0] if embeddings else []


__all__ = [
    "get_openai_client",
    "generate_embeddings_batch",
    "generate_embedding_single",
]
