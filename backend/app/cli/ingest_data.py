"""
CLI command for ingesting data from JSON files.
"""

import asyncio
import argparse
import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.services.data_loader import load_all_data
from app.services.document_compiler import compile_all_documents_for_store
from app.services.chroma_service import add_documents, delete_collection
from app.services.embedding_service import generate_embeddings_batch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def ingest_data(
    data_dir: Path,
    store_id: str,
    postgres_only: bool = False,
    chroma_only: bool = False,
    skip_embeddings: bool = False,
) -> None:
    """
    Ingest data from JSON files.

    Args:
        data_dir: Path to data directory
        store_id: Store ID
        postgres_only: Only load into PostgreSQL
        chroma_only: Only load into Chroma
        skip_embeddings: Skip embedding generation (use Chroma's default)
    """
    async with AsyncSessionLocal() as session:
        if not chroma_only:
            logger.info("=" * 80)
            logger.info("Loading data into PostgreSQL...")
            logger.info("=" * 80)

            results = await load_all_data(session, data_dir, store_id, skip_chroma=True)

            logger.info("=" * 80)
            logger.info("Data loading summary:")
            for data_type, count in results.items():
                logger.info(f"  {data_type}: {count} records")
            logger.info("=" * 80)

        if not postgres_only:
            logger.info("=" * 80)
            logger.info("Compiling documents for Chroma...")
            logger.info("=" * 80)

            # Delete existing collection if it exists
            try:
                delete_collection(store_id)
                logger.info(f"Deleted existing collection for store {store_id}")
            except Exception as e:
                logger.debug(f"Collection may not exist: {e}")

            # Compile documents from PostgreSQL
            documents = await compile_all_documents_for_store(session, store_id)

            if documents:
                logger.info(f"Compiled {len(documents)} documents")

                # Extract texts and metadata
                texts = [doc["text"] for doc in documents]
                metadatas = [doc["metadata"] for doc in documents]
                ids = [
                    f"{doc['metadata']['content_type']}_{doc['metadata']['content_id']}"
                    for doc in documents
                ]

                # Generate embeddings if not skipping
                embeddings = None
                if not skip_embeddings:
                    logger.info("Generating embeddings...")
                    embeddings = generate_embeddings_batch(texts, batch_size=100)
                    logger.info(f"Generated {len(embeddings)} embeddings")

                # Add to Chroma
                logger.info("Adding documents to Chroma...")
                add_documents(
                    store_id=store_id,
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids,
                )
                logger.info(f"Successfully added {len(documents)} documents to Chroma")
            else:
                logger.warning("No documents compiled")

            logger.info("=" * 80)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Ingest data from JSON files")
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Path to data directory containing JSON files",
    )
    parser.add_argument(
        "--store-id",
        type=str,
        required=True,
        help="Store ID for multi-tenant filtering",
    )
    parser.add_argument(
        "--postgres-only",
        action="store_true",
        help="Only load data into PostgreSQL",
    )
    parser.add_argument(
        "--chroma-only",
        action="store_true",
        help="Only load data into Chroma (requires PostgreSQL data)",
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip embedding generation (use Chroma's default)",
    )

    args = parser.parse_args()

    if not args.data_dir.exists():
        logger.error(f"Data directory does not exist: {args.data_dir}")
        return

    asyncio.run(
        ingest_data(
            data_dir=args.data_dir,
            store_id=args.store_id,
            postgres_only=args.postgres_only,
            chroma_only=args.chroma_only,
            skip_embeddings=args.skip_embeddings,
        )
    )


if __name__ == "__main__":
    main()
