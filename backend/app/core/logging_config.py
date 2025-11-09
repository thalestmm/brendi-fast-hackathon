"""
Centralized logging configuration for the application.
Configures logging to both console and file outputs with proper formatting and rotation.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(
    log_level: str = "DEBUG",
    log_file_path: Optional[str] = None,
    service_name: str = "app",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Configure logging for the application with both console and file handlers.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file_path: Path to the log file. If None, only console logging is enabled.
        service_name: Name of the service (used for logger name)
        max_bytes: Maximum size of each log file before rotation (default 10MB)
        backup_count: Number of backup files to keep (default 5)

    Returns:
        Configured logger instance
    """
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation (if log file path is provided)
    if log_file_path:
        try:
            log_path = Path(log_file_path)

            if log_path.suffix:
                # Looks like a file path, ensure parent directory exists
                log_path.parent.mkdir(parents=True, exist_ok=True)
                resolved_log_path = log_path
            else:
                # Treat as directory and create a file name based on the service
                log_path.mkdir(parents=True, exist_ok=True)
                resolved_log_path = log_path / f"{service_name}.log"

            file_handler = RotatingFileHandler(
                filename=str(resolved_log_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(getattr(logging, log_level.upper()))
            file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(file_handler)

            root_logger.info(f"File logging enabled: {resolved_log_path}")
            root_logger.info(
                f"Log rotation: max_bytes={max_bytes}, backup_count={backup_count}"
            )

        except Exception as e:
            root_logger.error(f"Failed to setup file logging: {e}")
            root_logger.warning("Continuing with console logging only")

    # Create a named logger for the service
    service_logger = logging.getLogger(service_name)

    return service_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.

    Args:
        name: Name of the logger (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
