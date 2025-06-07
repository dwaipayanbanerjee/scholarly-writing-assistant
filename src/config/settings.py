"""Unified application configuration using *Pydantic*.

This file consolidates the former ``constants.py`` and ``config.py`` data into a
single, validated settings object.  The original modules continue to exist but
now simply re-export values from :pydata:`settings`, so existing imports remain
back-compatible.
"""

from __future__ import annotations

from typing import Any, Dict, List

# Ensure .env file is loaded before BaseSettings reads environment variables.
try:
    from dotenv import load_dotenv

    load_dotenv()  # load from default .env path if present
except ModuleNotFoundError:  # pragma: no cover – optional dependency
    pass

try:
    # Pydantic < 2.2
    from pydantic import BaseSettings, Field, root_validator  # type: ignore
except ImportError:  # pragma: no cover – Pydantic ≥2.2 relocated BaseSettings
    try:
        from pydantic_settings import BaseSettings  # type: ignore
        from pydantic import Field, root_validator  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover – minimal fallback
        # Minimal fallback so that the application can still start in
        # environments where `pydantic-settings` is not available yet (for
        # instance, before an updated *requirements.txt* has been installed).
        from pydantic import Field, root_validator  # type: ignore

        class _FallbackBaseSettings:  # pylint: disable=too-few-public-methods
            pass

        BaseSettings = _FallbackBaseSettings  # type: ignore


class Settings(BaseSettings):
    # ------------------------------------------------------------------
    # API keys (read from environment / .env)
    # ------------------------------------------------------------------
    OPENAI_API_KEY: str | None = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = Field(default=None, env="ANTHROPIC_API_KEY")
    GEMINI_API_KEY: str | None = Field(default=None, env="GEMINI_API_KEY")

    # ------------------------------------------------------------------
    # UI constants (formerly constants.py)
    # ------------------------------------------------------------------
    DEFAULT_FONT_FAMILY: str = "Verdana"
    DEFAULT_FONT_SIZE: int = 22
    GUI_FONT_SIZE: int = 14
    LINE_SPACING_PERCENT: int = 120
    DEFAULT_TEMPERATURE: float = 0.7

    MIN_WINDOW_WIDTH: int = 1000
    MIN_WINDOW_HEIGHT: int = 700

    TEXT_LAYOUT_RATIO: int = 7
    CONTROL_PANEL_RATIO: int = 3

    SPLITTER_LEFT_SIZE: int = 500
    SPLITTER_RIGHT_SIZE: int = 500

    TEMPERATURE_MIN: int = 0
    TEMPERATURE_MAX: int = 100

    TOKEN_EXPANSION_SMALL: float = 1.2  # For inputs < 100 tokens
    TOKEN_EXPANSION_MEDIUM: float = 1.1  # For inputs < 500 tokens
    TOKEN_EXPANSION_LARGE: float = 1.05  # For inputs >= 500 tokens
    TOKEN_BUFFER_FACTOR: float = 1.05

    TOKEN_THRESHOLD_SMALL: int = 100
    TOKEN_THRESHOLD_MEDIUM: int = 500

    CLAUDE_MAX_TOKENS: int = 8192
    TOKEN_COST_DIVISOR: int = 1_000_000  # For per-million token costs

    OUTPUT_DATE_FORMAT: str = "%Y%m%d%H%M%S"
    OUTPUT_FILE_PREFIX: str = "output-"
    OUTPUT_FILE_EXTENSION: str = ".txt"

    # ------------------------------------------------------------------
    # Model / pricing data (formerly config.py)
    # ------------------------------------------------------------------
    MODEL_CHOICES: List[str] = [
        "claude-opus-4-20250514",
        "claude-sonnet-4-20250514",
        "claude-3-7-sonnet-20250219",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4.1-nano",
        "gpt-4.5-preview",
        "o3-mini",
        "o4-mini-high",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
    ]

    MAX_OUTPUT_TOKENS: Dict[str, int] = {
        "claude-opus-4-20250514": 32000,
        "claude-sonnet-4-20250514": 64000,
        "claude-3-7-sonnet-20250219": 64000,
        "gpt-4.1": 32768,
        "gpt-4.1-mini": 32768,
        "gpt-4.1-nano": 32768,
        "gpt-4.5-preview": 32768,
        "o3-mini": 100000,
        "o4-mini-high": 100000,
        "gemini-2.5-pro": 8192,
        "gemini-2.5-flash": 8192,
    }

    MAX_CONTEXT_WINDOW: Dict[str, int] = {
        "claude-opus-4-20250514": 200000,
        "claude-sonnet-4-20250514": 200000,
        "claude-3-7-sonnet-20250219": 200000,
        "gpt-4.1": 1000000,
        "gpt-4.1-mini": 1000000,
        "gpt-4.1-nano": 1000000,
        "gpt-4.5-preview": 256000,
        "o3-mini": 200000,
        "o4-mini-high": 200000,
        "gemini-2.5-pro": 1000000,
        "gemini-2.5-flash": 1000000,
    }

    COST_PER_1M_TOKENS: Dict[str, Dict[str, float]] = {
        "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
        "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
        "claude-3-7-sonnet-20250219": {"input": 3.00, "output": 15.00},
        "gpt-4.1": {"input": 2.00, "output": 8.00},
        "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
        "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
        "gpt-4.5-preview": {"input": 75.00, "output": 150.00},
        "o3-mini": {"input": 1.00, "output": 4.00},
        "o4-mini-high": {"input": 1.00, "output": 4.00},
        "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
        "gemini-2.5-flash": {"input": 0.50, "output": 2.00},
    }

    SYSTEM_MESSAGE: str = (
        """You are a meticulous editor with a keen eye for detail, specializing in refining academic texts. Your task is to enhance the clarity, readability, and stylistic flow of the provided text while rigorously preserving its original meaning, scholarly tone, and the author's voice.

Follow these precise guidelines:

1. **Scholarly Analysis:** Carefully examine the text's structure, argumentation, and content. Identify areas where clarity could be improved, the flow could be smoother, and the style could be subtly enhanced. Pay close attention to the author's voice and maintain the formal, academic tone.

2. **Clarity and Precision:**  Refine sentence structure for optimal clarity. Deconstruct any overly complex sentences, ensuring each thought is expressed with precision. Favor the active voice when it enhances clarity and directness, but maintain a balance appropriate for scholarly writing. Take calculated risks to improve readability without sacrificing academic rigor.

3. **Subtle Stylistic Enhancement:**  While maintaining the formal tone, make judicious stylistic adjustments to enhance the text's flow and engagement. Preserve the author's voice, ensuring consistency throughout. Vary sentence length and structure strategically to create a more dynamic reading experience, appropriate for the subject matter. Allow longer sentences when they contribute to the intellectual depth and nuance of the argument.

4. **Logical Flow and Coherence:**  Ensure a smooth and logical progression of ideas throughout the text. Strengthen transitions where needed to create a cohesive and compelling narrative. Maintain a high level of coherence, ensuring that each paragraph and section contributes to a unified argument.

5. **Preservation of Meaning:**  Uphold the integrity of the original content. Every piece of information, every citation, and every nuance of meaning must be meticulously preserved. Your revisions must accurately reflect the author's original intent and argument.

6. **Presentation:**  Return the improved text directly, preserving the original paragraph structure and meaningful line breaks. Avoid adding any extraneous formatting. Your goal is a polished, refined text that exemplifies the highest standards of scholarly writing."""
    )

    USER_MESSAGE_TEMPLATE: str = (
        """<text_to_revise>
{text}
</text_to_revise>

Please revise this text according to the provided instructions."""
    )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    # Validation hook – only executed when *pydantic* is available.
    try:
        _root_validator = root_validator  # noqa: N818 – alias for conditional definition

        @_root_validator(skip_on_failure=True)  # type: ignore[misc]
        def _check_api_keys(cls, values: Dict[str, Any]) -> Dict[str, Any]:  # noqa: N805
            if not (
                values.get("OPENAI_API_KEY")
                or values.get("ANTHROPIC_API_KEY")
                or values.get("GEMINI_API_KEY")
            ):
                raise ValueError(
                    "No API keys configured. Please set at least one of OPENAI_API_KEY, "
                    "ANTHROPIC_API_KEY or GEMINI_API_KEY in the environment/.env file."
                )
            return values
    except NameError:
        # If pydantic isn't importable we're already using the fallback class – skip validation.
        pass


# Singleton instance
settings = Settings()  # type: ignore[arg-type]
