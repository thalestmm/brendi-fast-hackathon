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


    logger.info("FastAPI backend application started successfully")

    yield

    logger.info("=" * 80)
    logger.info("Stopping FastAPI backend application")
    logger.info("=" * 80)

app : FastAPI = FastAPI(
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

from app.routers import router as main_router # noqa: E402

app.include_router(main_router)

@app.get("/")
async def root():
    """
    Root endpoint for the FastAPI application.
    """
    if settings.ENVIRONMENT != "production":
        return RedirectResponse(url="/docs")
    return JSONResponse(content={"message": "Brendi Fast Hackathon API", "status": "ok"}, status_code=status.HTTP_200_OK)

@app.get("/health")
async def health():
    """
    Health check endpoint for the FastAPI application.
    """
    # TODO: Add health check as kubernetes liveness probe
    return JSONResponse(content={"message": "Brendi Fast Hackathon API is healthy", "status": "ok"}, status_code=status.HTTP_200_OK)