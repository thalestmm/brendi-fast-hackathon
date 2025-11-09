"""
Main entry point for the FastAPI application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.database import check_database_health, AsyncSessionLocal
from app.middleware.tenant import TenantMiddleware
from app.services.data_loader import load_all_data
from app.services.document_compiler import compile_all_documents_for_store
from app.services.chroma_service import add_documents, delete_collection
from app.services.embedding_service import generate_embeddings_batch


logger = setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file_path=settings.LOG_DIR,
    service_name="backend",
    max_bytes=settings.LOG_FILE_MAX_BYTES,
    backup_count=settings.LOG_FILE_BACKUP_COUNT,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan for the FastAPI application.
    """
    logger.info("=" * 80)
    logger.info("Starting FastAPI backend application")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("=" * 80)

    if settings.ENVIRONMENT == "development":
        logger.info("Environment variables: ")
        for key, value in settings.model_dump().items():
            logger.info(f"{key}: {value}")
        logger.info("=" * 80)

    # Data ingestion on startup
    if settings.AUTO_INGEST_DATA:
        try:
            if settings.DATA_DIR.exists():
                logger.info("=" * 80)
                logger.info("Starting automatic data ingestion...")
                logger.info(f"Data directory: {settings.DATA_DIR}")
                logger.info(f"Store ID: {settings.STORE_ID}")
                logger.info("=" * 80)

                async with AsyncSessionLocal() as session:
                    # Load data into PostgreSQL
                    logger.info("Loading data into PostgreSQL...")
                    try:
                        results = await load_all_data(
                            session, settings.DATA_DIR, settings.STORE_ID, skip_chroma=True
                        )

                        logger.info("Data loading summary:")
                        for data_type, count in results.items():
                            logger.info(f"  {data_type}: {count} records")
                    except Exception as e:
                        logger.error(f"Error during data loading: {e}", exc_info=True)
                        logger.warning("Continuing with document compilation despite errors")
                        results = {}

                    # Compile documents for Chroma
                    logger.info("Compiling documents for Chroma...")
                    try:
                        delete_collection(settings.STORE_ID)
                        logger.info(
                            f"Deleted existing collection for store {settings.STORE_ID}"
                        )
                    except Exception:
                        logger.debug("Collection may not exist")

                    documents = await compile_all_documents_for_store(
                        session, settings.STORE_ID
                    )

                    if documents:
                        texts = [doc["text"] for doc in documents]
                        metadatas = [doc["metadata"] for doc in documents]
                        ids = [
                            f"{doc['metadata']['content_type']}_{doc['metadata']['content_id']}"
                            for doc in documents
                        ]

                        logger.info("Generating embeddings...")
                        embeddings = generate_embeddings_batch(texts, batch_size=100)

                        logger.info("Adding documents to Chroma...")
                        add_documents(
                            store_id=settings.STORE_ID,
                            documents=texts,
                            embeddings=embeddings,
                            metadatas=metadatas,
                            ids=ids,
                        )
                        logger.info(
                            f"Successfully added {len(documents)} documents to Chroma"
                        )

                logger.info("=" * 80)
                logger.info("Data ingestion completed successfully")
                logger.info("=" * 80)
            else:
                logger.warning(f"Data directory does not exist: {settings.DATA_DIR}")
                logger.warning("Skipping automatic data ingestion")
        except Exception as e:
            logger.error(f"Error during data ingestion: {e}", exc_info=True)
            logger.error("Continuing with server startup despite ingestion error")
    else:
        logger.info("Automatic data ingestion is disabled (AUTO_INGEST_DATA=False)")

    logger.info("FastAPI backend application started successfully")

    yield

    logger.info("=" * 80)
    logger.info("Stopping FastAPI backend application")
    logger.info("=" * 80)


app: FastAPI = FastAPI(
    title="Brendi Fast Hackathon",
    description="Backend for the Brendi Fast Hackathon",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant middleware
app.add_middleware(TenantMiddleware)

from app.routers import router as main_router  # noqa: E402

app.include_router(main_router)


@app.get("/")
async def root():
    """
    Root endpoint for the FastAPI application.
    """
    if settings.ENVIRONMENT != "production":
        return RedirectResponse(url="/docs")
    return JSONResponse(
        content={"message": "Brendi Fast Hackathon API", "status": "ok"},
        status_code=status.HTTP_200_OK,
    )


@app.get("/health")
async def health():
    """
    Health check endpoint for the FastAPI application.
    """
    db_healthy = await check_database_health()

    health_status = {
        "status": "ok" if db_healthy else "degraded",
        "database": "healthy" if db_healthy else "unhealthy",
        "message": "Brendi Fast Hackathon API is healthy"
        if db_healthy
        else "Database connection failed",
    }

    status_code = (
        status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(content=health_status, status_code=status_code)
