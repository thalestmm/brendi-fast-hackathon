import logging
from pathlib import Path
from typing import Any, Optional, Literal

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

    model_config = ConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

settings = Settings()

__all__ = ["settings"]
