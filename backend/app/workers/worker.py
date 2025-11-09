"""
RQ Worker for processing background jobs, including buffered messages.
"""

import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rq import Worker, Queue, Connection
from rq.job import Job

from app.core.redis import get_redis_connection
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def process_job_exception(job: Job, exc_type, exc_value, traceback):
    """
    Handle exceptions in job processing.
    
    Args:
        job: The RQ job that failed
        exc_type: Exception type
        exc_value: Exception value
        traceback: Traceback object
    """
    logger.error(
        f"Job {job.id} failed: {exc_type.__name__}: {exc_value}",
        exc_info=(exc_type, exc_value, traceback),
    )


def main():
    """Start the RQ worker."""
    redis_conn = get_redis_connection()
    queue = Queue(settings.RQ_QUEUE_NAME, connection=redis_conn)
    
    logger.info(f"Starting RQ worker for queue: {settings.RQ_QUEUE_NAME}")
    logger.info(f"Redis connection: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    
    with Connection(redis_conn):
        worker = Worker(
            [queue],
            name=f"message-worker-{os.getpid()}",
            exception_handlers=[process_job_exception],
        )
        worker.work()


if __name__ == "__main__":
    main()

