"""
Data management API schemas.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class DataStatusResponse(BaseModel):
    """Data ingestion status response."""

    store_id: str
    postgres_counts: Dict[str, int]
    chroma_document_count: int
    last_updated: Optional[str]


class ReindexRequest(BaseModel):
    """Request to reindex Chroma from PostgreSQL."""

    store_id: str
    skip_embeddings: bool = False
