# validators.py
"""
Validation functions for the Writing Assistant application.
"""

from typing import Optional


def is_supported_model(model: str) -> bool:
    """Check if a model is supported by the application."""
    supported_prefixes = ("o1-", "gpt-", "claude-", "gem")
    return model.startswith(supported_prefixes)


def get_model_type(model: str) -> Optional[str]:
    """Get the type/provider of a model based on its name."""
    if model.startswith(("o1-", "gpt-")):
        return "openai"
    elif model.startswith("claude-"):
        return "anthropic"
    elif model.startswith("gem"):
        return "gemini"
    return None