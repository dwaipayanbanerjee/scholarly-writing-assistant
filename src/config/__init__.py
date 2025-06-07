"""Convenience re-exports for configuration values.

New code should import from :pydata:`src.config.settings.settings` directly but
existing imports that expect to find names on ``src.config`` will continue to
work thanks to these re-exports.
"""

from __future__ import annotations

from .settings import settings  # Singleton settings object

from .config import (  # noqa: F401 – Re-export for backward compatibility
    MODEL_CHOICES,
    MAX_OUTPUT_TOKENS,
    MAX_CONTEXT_WINDOW,
    COST_PER_1M_TOKENS,
    SYSTEM_MESSAGE,
    USER_MESSAGE_TEMPLATE,
)

from .constants import *  # noqa: F403 – export UI constants

__all__ = [
    "settings",
    "MODEL_CHOICES",
    "MAX_OUTPUT_TOKENS",
    "MAX_CONTEXT_WINDOW",
    "COST_PER_1M_TOKENS",
    "SYSTEM_MESSAGE",
    "USER_MESSAGE_TEMPLATE",
] + [name for name in globals().keys() if name.isupper()]
