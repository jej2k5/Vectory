"""Loguru logger configuration for the Vectory application."""

from __future__ import annotations

import sys

from loguru import logger

from app.config import settings


def setup_logger() -> None:
    """Configure the loguru logger.

    Removes any default handlers and adds a single stderr handler whose
    level is controlled by the ``LOG_LEVEL`` environment variable.
    """
    logger.remove()

    log_level = settings.LOG_LEVEL.upper()

    logger.add(
        sys.stderr,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        backtrace=True,
        diagnose=True,
        enqueue=True,  # thread-safe logging
    )

    logger.info("Logger initialised at level {}", log_level)


# Run setup on first import so callers can simply ``from app.utils.logger import logger``.
setup_logger()

__all__ = ["logger", "setup_logger"]
