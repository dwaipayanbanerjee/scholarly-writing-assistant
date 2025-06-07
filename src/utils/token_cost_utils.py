# ---------------------------------------------------------------------------
# Token counting & cost utilities
# ---------------------------------------------------------------------------

from typing import Dict, Any

try:
    import tiktoken  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – allow running without tiktoken
    tiktoken = None  # type: ignore

try:
    import google.generativeai as genai  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – allow running without gemini SDK
    genai = None  # type: ignore

from src.config.config import COST_PER_1M_TOKENS, MAX_OUTPUT_TOKENS
from src.config.constants import (
    TOKEN_EXPANSION_SMALL,
    TOKEN_EXPANSION_MEDIUM,
    TOKEN_EXPANSION_LARGE,
    TOKEN_BUFFER_FACTOR,
    TOKEN_THRESHOLD_SMALL,
    TOKEN_THRESHOLD_MEDIUM,
    TOKEN_COST_DIVISOR,
)

from src.utils.logger import logger

# In-memory caches – these live for the lifetime of the process and speed up
# repeated calls considerably.
from typing import Any

_ENCODER_CACHE: dict[str, Any] = {}
_GEMINI_MODEL_CACHE: dict[str, Any] = {}

def estimate_tokens(text: str, model: str) -> int:
    """Estimate the number of tokens in the given text for the specified model."""
    if model.startswith(("gpt-", "o1-")):
        # Cache encoding lookup – tiktoken call can take ~20 ms on first use.
        if tiktoken is None:
            # Crude fallback: average 4 characters per token
            return max(1, len(text) // 4)

        try:
            encoding = _ENCODER_CACHE[model]
        except KeyError:
            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                logger.warning("Unknown model '%s' – falling back to cl100k_base encoder", model)
                encoding = tiktoken.get_encoding("cl100k_base")
            _ENCODER_CACHE[model] = encoding

        return len(encoding.encode(text))
    elif model.startswith("claude-"):
        # Import here to avoid circular dependency
        from src.api.api_clients import api_clients
        client = api_clients.get_anthropic_client()
        token_count = client.count_tokens(text)
        return token_count
    elif model.startswith("gem"):
        if genai is None:
            return max(1, len(text) // 4)

        try:
            counting_model = _GEMINI_MODEL_CACHE.get(model)
            if counting_model is None:  # pragma: no cover – first call per model
                counting_model = genai.GenerativeModel(model_name=model)
                _GEMINI_MODEL_CACHE[model] = counting_model
            return counting_model.count_tokens(text).total_tokens
        except Exception as exc:  # pragma: no cover – network/unavailable
            logger.warning("Gemini token count failed: %s", exc)
            return max(1, len(text) // 4)
    else:
        raise ValueError(f"Unsupported model: {model}")

def calculate_cost(model: str, input_text: str, system_message: str) -> Dict[str, Any]:
    """Calculate the estimated cost for processing the text."""
    if model not in COST_PER_1M_TOKENS:
        raise ValueError(f"Cost information not available for model: {model}")

    input_tokens = estimate_tokens(system_message + "\n\n" + input_text, model)
    estimated_output_tokens = estimate_output_tokens(input_text, model)

    input_cost = (input_tokens / TOKEN_COST_DIVISOR) * COST_PER_1M_TOKENS[model]["input"]
    output_cost = (estimated_output_tokens / TOKEN_COST_DIVISOR) * COST_PER_1M_TOKENS[model]["output"]

    total_cost = input_cost + output_cost
    total_tokens = input_tokens + estimated_output_tokens

    logger.debug(
        f"Cost calculation - Model: {model}, Input Tokens: {input_tokens}, "
        f"Estimated Output Tokens: {estimated_output_tokens}, Total Cost: ${total_cost:.6f}"
    )

    return {
        "model": model,
        "input_tokens": input_tokens,
        "estimated_output_tokens": estimated_output_tokens,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
    }

def calculate_cost_from_usage(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate the actual cost based on token usage."""
    if model not in COST_PER_1M_TOKENS:
        return 0

    input_cost = (input_tokens / TOKEN_COST_DIVISOR) * COST_PER_1M_TOKENS[model]["input"]
    output_cost = (output_tokens / TOKEN_COST_DIVISOR) * COST_PER_1M_TOKENS[model]["output"]

    logger.debug(
        f"Calculate from usage - Model: {model}, Input Tokens: {input_tokens}, "
        f"Output Tokens: {output_tokens}, Input Cost=${input_cost:.6f}, Output Cost=${output_cost:.6f}"
    )

    return input_cost + output_cost

def estimate_output_tokens(text: str, model: str) -> int:
    """Estimate the number of output tokens based on input text and model."""
    input_tokens = estimate_tokens(text, model)

    # Use a sliding scale: longer inputs are less likely to expand as much
    if input_tokens < TOKEN_THRESHOLD_SMALL:
        expansion_factor = TOKEN_EXPANSION_SMALL
    elif input_tokens < TOKEN_THRESHOLD_MEDIUM:
        expansion_factor = TOKEN_EXPANSION_MEDIUM
    else:
        expansion_factor = TOKEN_EXPANSION_LARGE

    estimated_output = int(input_tokens * expansion_factor)

    # Add a small buffer for potential variations
    estimated_output = int(estimated_output * TOKEN_BUFFER_FACTOR)

    # Respect max tokens for the model
    max_output = MAX_OUTPUT_TOKENS.get(model, float("inf"))
    estimated_output = min(estimated_output, max_output)

    logger.debug(
        f"Estimate Output Tokens - Input Tokens: {input_tokens}, "
        f"Estimated Output Tokens: {estimated_output}"
    )

    return estimated_output