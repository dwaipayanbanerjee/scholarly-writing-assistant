"""Backward-compatibility shim.

The codebase originally imported numerous *mutable* constants from this module.
All those values now live on :pydata:`src.config.settings.settings`.  In order
not to break existing imports we simply re-export them here.
"""

from __future__ import annotations

from typing import Any

from .settings import settings as _s


def _export(name: str) -> Any:  # type: ignore[return-type]
    return getattr(_s, name)


# UI constants
DEFAULT_FONT_FAMILY = _export("DEFAULT_FONT_FAMILY")
DEFAULT_FONT_SIZE = _export("DEFAULT_FONT_SIZE")
GUI_FONT_SIZE = _export("GUI_FONT_SIZE")
LINE_SPACING_PERCENT = _export("LINE_SPACING_PERCENT")
DEFAULT_TEMPERATURE = _export("DEFAULT_TEMPERATURE")

MIN_WINDOW_WIDTH = _export("MIN_WINDOW_WIDTH")
MIN_WINDOW_HEIGHT = _export("MIN_WINDOW_HEIGHT")

TEXT_LAYOUT_RATIO = _export("TEXT_LAYOUT_RATIO")
CONTROL_PANEL_RATIO = _export("CONTROL_PANEL_RATIO")

SPLITTER_LEFT_SIZE = _export("SPLITTER_LEFT_SIZE")
SPLITTER_RIGHT_SIZE = _export("SPLITTER_RIGHT_SIZE")

TEMPERATURE_MIN = _export("TEMPERATURE_MIN")
TEMPERATURE_MAX = _export("TEMPERATURE_MAX")

TOKEN_EXPANSION_SMALL = _export("TOKEN_EXPANSION_SMALL")
TOKEN_EXPANSION_MEDIUM = _export("TOKEN_EXPANSION_MEDIUM")
TOKEN_EXPANSION_LARGE = _export("TOKEN_EXPANSION_LARGE")
TOKEN_BUFFER_FACTOR = _export("TOKEN_BUFFER_FACTOR")

TOKEN_THRESHOLD_SMALL = _export("TOKEN_THRESHOLD_SMALL")
TOKEN_THRESHOLD_MEDIUM = _export("TOKEN_THRESHOLD_MEDIUM")

CLAUDE_MAX_TOKENS = _export("CLAUDE_MAX_TOKENS")
TOKEN_COST_DIVISOR = _export("TOKEN_COST_DIVISOR")

OUTPUT_DATE_FORMAT = _export("OUTPUT_DATE_FORMAT")
OUTPUT_FILE_PREFIX = _export("OUTPUT_FILE_PREFIX")
OUTPUT_FILE_EXTENSION = _export("OUTPUT_FILE_EXTENSION")

__all__ = [name for name in globals().keys() if not name.startswith("_")]
