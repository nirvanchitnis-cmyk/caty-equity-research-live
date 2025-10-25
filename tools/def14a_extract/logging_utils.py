"""Structured logging helpers."""

from __future__ import annotations

import logging
from typing import Any, Mapping


LOGGER_NAME = "def14a_extract"


def get_logger(name: str = LOGGER_NAME) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_event(
    message: str,
    *,
    level: int = logging.INFO,
    **extra: Mapping[str, Any],
) -> None:
    logger = get_logger()
    if extra:
        message = f"{message} | {dict(extra)}"
    logger.log(level, message)
