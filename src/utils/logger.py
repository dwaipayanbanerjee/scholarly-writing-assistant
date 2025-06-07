"""Centralised logging configuration used across the Writing Assistant project.

Importing ``logger`` from this module guarantees that:

1. Logging is configured exactly once.
2. A consistent format is used across every file.
3. Duplicate handlers are avoided even when modules are re-imported (e.g. in
   interactive sessions).
"""

from __future__ import annotations

import logging
import os


def _create_logger() -> logging.Logger:
    """Return the shared application logger instance.

    The logger is configured only the first time this function is called. On
    subsequent imports the same instance (with its pre-attached handler) is
    returned, preventing duplicate log lines.
    """

    logger_name = "writing_assistant"
    logger = logging.getLogger(logger_name)

    # Configure only once.
    if not logger.handlers:
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_str, logging.INFO)
        logger.setLevel(level)

        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        )
        logger.addHandler(handler)

        # Prevent message propagation to the root logger which could otherwise
        # duplicate lines if the root logger is configured elsewhere.
        logger.propagate = False

    return logger


# Exported, shared logger instance.
logger = _create_logger()
