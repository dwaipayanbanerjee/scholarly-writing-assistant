"""Backward-compatibility shim for legacy ``src.config.config`` imports.

All configuration values now live in :pydata:`src.config.settings.settings`.
This module re-exports them so that the rest of the application keeps working
unchanged.
"""

from __future__ import annotations

from typing import Any

from .settings import settings as _s


def _export(name: str) -> Any:  # type: ignore[return-type]
    return getattr(_s, name)


MODEL_CHOICES = _export("MODEL_CHOICES")
MAX_OUTPUT_TOKENS = _export("MAX_OUTPUT_TOKENS")
MAX_CONTEXT_WINDOW = _export("MAX_CONTEXT_WINDOW")
COST_PER_1M_TOKENS = _export("COST_PER_1M_TOKENS")
SYSTEM_MESSAGE = _export("SYSTEM_MESSAGE")
USER_MESSAGE_TEMPLATE = _export("USER_MESSAGE_TEMPLATE")

__all__ = [
    "MODEL_CHOICES",
    "MAX_OUTPUT_TOKENS",
    "MAX_CONTEXT_WINDOW",
    "COST_PER_1M_TOKENS",
    "SYSTEM_MESSAGE",
    "USER_MESSAGE_TEMPLATE",
]
