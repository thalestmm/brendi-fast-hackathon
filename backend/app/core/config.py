import logging
from pathlib import Path
from typing import Optional, Literal

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """
    Central application settings with layered environment support.
    """

    # Environment configuration
    ENVIRONMENT: Literal["development", "testing", "staging", "production"] = Field(
        default="development"
    )
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="DEBUG"
    )

    # Logging configuration
    LOG_DIR: Path = Field(default=BASE_DIR / "logs")
    LOG_FILE_MAX_BYTES: int = Field(default=10 * 1024 * 1024)  # 10MB
    LOG_FILE_BACKUP_COUNT: int = Field(default=5)

    # LLM configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None)

    # LangSmith configuration
    LANGSMITH_PROJECT: Optional[str] = Field(default=None)
    LANGSMITH_API_KEY: Optional[str] = Field(default=None)
    LANGSMITH_TRACING_V2: bool = Field(default=True)

    # Redis configuration
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: Optional[str] = Field(default=None)

    # RQ configuration
    RQ_QUEUE_NAME: str = Field(default="default")
    WORKER_QUEUES: list[str] = Field(default_factory=lambda: ["default"])
    WORKER_TIMEOUT: int = Field(default=300)  # 5 minutes

    # ChromaDB Configuration
    CHROMA_HOST: Optional[str] = Field(default="chroma")
    CHROMA_PORT: Optional[int] = Field(default=8000)
    CHROMA_API_TOKEN: Optional[str] = Field(default="admin")
    CHROMA_COLLECTION_NAME: Optional[str] = Field(default="rag_data")

    # PostgreSQL configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/brendi_db"
    )
    DB_POOL_SIZE: int = Field(default=5)
    DB_MAX_OVERFLOW: int = Field(default=10)

    # Data ingestion configuration
    DATA_DIR: Path = Field(default=BASE_DIR.parent / "data")
    STORE_ID: str = Field(default="0WcZ1MWEaFc1VftEBdLa")
    AUTO_INGEST_DATA: bool = Field(default=False)

    # Agent configuration
    AGENT_MESSAGE_HISTORY_LIMIT: int = Field(default=10)

    # Message buffering configuration
    MESSAGE_BUFFER_TIMEOUT_SECONDS: int = Field(
        default=2,
        description="Wait time in seconds before processing buffered messages",
    )

    model_config = ConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()

__all__ = ["settings"]
