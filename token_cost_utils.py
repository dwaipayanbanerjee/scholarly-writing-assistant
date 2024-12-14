import tiktoken
import logging
from config import COST_PER_1M_TOKENS, MAX_OUTPUT_TOKENS
import anthropic
import google.generativeai as genai

anthropic_client = anthropic.Client()

# Configure logging
logger = logging.getLogger("token_cost_utils")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

def estimate_tokens(text: str, model: str) -> int:
    """Estimate the number of tokens in the given text for the specified model."""
    if model.startswith(("gpt-", "o1-")):
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    elif model.startswith("claude-"):
        token_count = anthropic_client.count_tokens(text)
        return token_count
    elif model.startswith("gem"):
        try:
            counting_model = genai.GenerativeModel(model_name=model)
            total_tokens = counting_model.count_tokens(text)
            total_tokens = total_tokens.total_tokens
            return total_tokens
        except:
            return 0
    else:
        raise ValueError(f"Unsupported model: {model}")

def calculate_cost(model: str, input_text: str, system_message: str):
    """Calculate the estimated cost for processing the text."""
    if model not in COST_PER_1M_TOKENS:
        raise ValueError(f"Cost information not available for model: {model}")

    input_tokens = estimate_tokens(system_message + "\n\n" + input_text, model)
    estimated_output_tokens = estimate_output_tokens(input_text, model)

    input_cost = (input_tokens / 1_000_000) * COST_PER_1M_TOKENS[model]["input"]
    output_cost = (estimated_output_tokens / 1_000_000) * COST_PER_1M_TOKENS[model]["output"]

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

    input_cost = (input_tokens / 1_000_000) * COST_PER_1M_TOKENS[model]["input"]
    output_cost = (output_tokens / 1_000_000) * COST_PER_1M_TOKENS[model]["output"]

    logger.debug(
        f"Calculate from usage - Model: {model}, Input Tokens: {input_tokens}, "
        f"Output Tokens: {output_tokens}, Input Cost=${input_cost:.6f}, Output Cost=${output_cost:.6f}"
    )

    return input_cost + output_cost

def estimate_output_tokens(text: str, model: str) -> int:
    """Estimate the number of output tokens based on input text and model."""
    input_tokens = estimate_tokens(text, model)

    # Use a sliding scale: longer inputs are less likely to expand as much
    if input_tokens < 100:
        expansion_factor = 1.2
    elif input_tokens < 500:
        expansion_factor = 1.1
    else:
        expansion_factor = 1.05

    estimated_output = int(input_tokens * expansion_factor)

    # Add a small buffer for potential variations
    estimated_output = int(estimated_output * 1.05)

    # Respect max tokens for the model
    max_output = MAX_OUTPUT_TOKENS.get(model, float("inf"))
    estimated_output = min(estimated_output, max_output)

    logger.debug(
        f"Estimate Output Tokens - Input Tokens: {input_tokens}, "
        f"Estimated Output Tokens: {estimated_output}"
    )

    return estimated_output