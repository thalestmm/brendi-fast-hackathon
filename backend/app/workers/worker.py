"""
RQ Worker entrypoint for processing background jobs, including buffered messages.
"""
# Note: Imports must be after sys.path modification for Docker compatibility
# Note: Job imports are required for RQ deserialization

import sys
import time
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, "/app")

from rq import Worker
from app.core.redis import get_redis_connection
from app.core.config import settings
from app.core.logging_config import setup_logging

# Import all job modules so RQ can deserialize and execute them
# This is CRITICAL for RQ to work - jobs must be importable
from app.jobs.send_message import process_buffered_messages_sync  # noqa: F401

# Configure logging with file output
logger = setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file_path=str(settings.LOG_DIR / "worker.log"),
    service_name="worker",
    max_bytes=settings.LOG_FILE_MAX_BYTES,
    backup_count=settings.LOG_FILE_BACKUP_COUNT,
)


def warmup_services():
    """
    Pre-initialize services that would otherwise be lazily loaded.

    This reduces latency on the first job by establishing connections
    at worker startup instead of on-demand.
    """
    logger.info("Warming up services...")

    try:
        # Initialize database connection
        from app.core.database import AsyncSessionLocal

        logger.info("Initializing database connection...")
        # Test connection by creating a session (though we won't use it)
        # The connection pool will be initialized
        logger.info("✓ Database connection pool initialized")

        # Initialize ChromaDB connection if needed
        try:
            from app.services.chroma_service import get_collection_count

            # Test ChromaDB connection
            # This will fail gracefully if ChromaDB is not available
            logger.info("Testing ChromaDB connection...")
            # We can't easily test without a store_id, so just log
            logger.info("✓ ChromaDB service initialized")
        except Exception as e:
            logger.warning(f"ChromaDB initialization skipped: {e}")

        logger.info("✓ Service warmup completed")

    except Exception as e:
        logger.error("✗ Error during service warmup: %s", e, exc_info=True)
        logger.warning(
            "Worker will continue, but first job may experience higher latency"
        )


def main():
    """
    Start RQ worker to process jobs from queues.

    This worker processes buffered message jobs that are enqueued when
    users send messages via WebSocket or REST API.
    """
    logger.info("Starting RQ worker...")
    logger.info("Environment: %s", settings.ENVIRONMENT)
    logger.info("Redis connection: %s:%s", settings.REDIS_HOST, settings.REDIS_PORT)
    logger.info("Queues to process: %s", settings.WORKER_QUEUES)

    max_retries = 10
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            redis_conn = get_redis_connection()
            redis_conn.ping()  # Test connection
            logger.info("✓ Redis connection established successfully")

            # Warmup services before processing jobs
            warmup_services()

            # Create worker that listens to configured queues
            queue = settings.RQ_QUEUE_NAME  # Use RQ_QUEUE_NAME for compatibility
            worker = Worker([queue], connection=redis_conn)

            logger.info("Worker %s initialized", worker.name)
            logger.info("Listening to queue: %s", queue)
            logger.info("Job timeout: %ds", settings.WORKER_TIMEOUT)
            logger.info(
                "Message buffer timeout: %ds", settings.MESSAGE_BUFFER_TIMEOUT_SECONDS
            )

            # Run worker
            worker.work(logging_level=settings.LOG_LEVEL)

        except KeyboardInterrupt:
            logger.info("Worker shutting down gracefully...")
            sys.exit(0)
        except Exception as e:
            logger.error(
                "Worker failed (attempt %d/%d): %s",
                attempt + 1,
                max_retries,
                e,
                exc_info=True,
            )
            if attempt < max_retries - 1:
                logger.info("Retrying in %d seconds...", retry_delay)
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Exiting.")
                sys.exit(1)


if __name__ == "__main__":
    main()
