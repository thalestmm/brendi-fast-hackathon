"""
Data management API endpoints.
"""

import logging
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func

from app.core.dependencies import DbSession, StoreId
from app.models import (
    Store,
    Order,
    Campaign,
    CampaignResult,
    Consumer,
    Feedback,
    MenuEvent,
)
from app.schemas.api.v1.data import DataStatusResponse, ReindexRequest
from app.services.chroma_service import get_collection_count, delete_collection
from app.services.document_compiler import compile_all_documents_for_store
from app.services.chroma_service import add_documents
from app.services.embedding_service import generate_embeddings_batch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/status", response_model=DataStatusResponse)
async def get_data_status(
    store_id: StoreId,
    db: DbSession,
) -> DataStatusResponse:
    """Get data ingestion status for a store."""
    try:
        # Count records in PostgreSQL
        postgres_counts = {}

        for model, name in [
            (Store, "stores"),
            (Order, "orders"),
            (Campaign, "campaigns"),
            (CampaignResult, "campaign_results"),
            (Consumer, "consumers"),
            (Feedback, "feedbacks"),
            (MenuEvent, "menu_events"),
        ]:
            stmt = select(func.count(model.id)).where(model.store_id == store_id)
            result = await db.execute(stmt)
            count = result.scalar() or 0
            postgres_counts[name] = count

        # Count documents in Chroma
        chroma_count = get_collection_count(store_id)

        return DataStatusResponse(
            store_id=store_id,
            postgres_counts=postgres_counts,
            chroma_document_count=chroma_count,
            last_updated=None,  # TODO: Track last update timestamp
        )
    except Exception as e:
        logger.error(f"Error getting data status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get data status",
        )


@router.post("/reindex-chroma")
async def reindex_chroma(
    store_id: StoreId,
    db: DbSession,
    request: ReindexRequest,
) -> Dict[str, str]:
    """
    Reindex Chroma collection from PostgreSQL data.

    This will delete the existing collection and rebuild it from PostgreSQL.
    """
    try:
        # Delete existing collection
        try:
            delete_collection(store_id)
            logger.info(f"Deleted existing collection for store {store_id}")
        except Exception as e:
            logger.debug(f"Collection may not exist: {e}")

        # Compile documents from PostgreSQL
        documents = await compile_all_documents_for_store(db, store_id)

        if documents:
            # Extract texts and metadata
            texts = [doc["text"] for doc in documents]
            metadatas = [doc["metadata"] for doc in documents]
            ids = [
                f"{doc['metadata']['content_type']}_{doc['metadata']['content_id']}"
                for doc in documents
            ]

            # Generate embeddings if not skipping
            embeddings = None
            if not request.skip_embeddings:
                logger.info("Generating embeddings...")
                embeddings = generate_embeddings_batch(texts, batch_size=100)

            # Add to Chroma
            add_documents(
                store_id=store_id,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )

            return {
                "status": "success",
                "message": f"Reindexed {len(documents)} documents for store {store_id}",
                "document_count": len(documents),
            }
        else:
            return {
                "status": "success",
                "message": "No documents found to index",
                "document_count": 0,
            }
    except Exception as e:
        logger.error(f"Error reindexing Chroma: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reindex Chroma: {str(e)}",
        )


@router.post("/load-all")
async def load_all_data_endpoint(
    store_id: StoreId,
    db: DbSession,
) -> Dict[str, Any]:
    """
    Load all data from JSON files into PostgreSQL.
    
    This endpoint is for development/debugging purposes.
    """
    from app.services.data_loader import load_all_data
    from app.core.config import settings
    
    try:
        results = await load_all_data(
            session=db,
            data_dir=settings.DATA_DIR,
            store_id=store_id,
            skip_chroma=True,
        )
        
        return {
            "status": "success",
            "message": f"Data loaded for store {store_id}",
            "results": results,
        }
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load data: {str(e)}",
        )
