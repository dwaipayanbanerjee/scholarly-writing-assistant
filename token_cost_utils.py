# token_cost_utils.py

import tiktoken
from typing import Dict, Tuple
from config import COST_PER_1M_TOKENS, MAX_OUTPUT_TOKENS
import anthropic
import google.generativeai as genai

anthropic_client = anthropic.Client()


def estimate_tokens(text: str, model: str) -> int:
    """Estimate the number of tokens in the given text for the specified model."""

    if model.startswith(("gpt-", "o1-")):
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))

    elif model.startswith("claude-"):
        token_count = anthropic_client.count_tokens(text)
        return token_count

    elif model == "gemini-1.5-pro":
        counting_model = genai.GenerativeModel(model_name=model)
        return counting_model.count_tokens(text)


def calculate_cost(
    model: str, input_text: str, system_message: str = "", recursive: bool = False
) -> Tuple[float, Dict[str, int]]:
    """
    Calculate the estimated cost and token usage for processing the given text.
    """
    if model not in COST_PER_1M_TOKENS:
        raise ValueError(f"Cost information not available for model: {model}")

    paragraphs = input_text.split("\n\n")
    total_input_tokens = 0
    total_output_tokens = 0

    if recursive:
        cumulative_text = system_message
        for para in paragraphs:
            cumulative_text += "\n\n" + para
            input_tokens = estimate_tokens(cumulative_text, model)
            output_tokens = estimate_tokens(para, model)
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
    else:
        full_input = system_message + "\n\n" + input_text
        total_input_tokens = estimate_tokens(full_input, model)
        total_output_tokens = estimate_tokens(input_text, model)

    # Add a buffer to output tokens and respect max tokens
    max_output = MAX_OUTPUT_TOKENS.get(model, float("inf"))
    total_output_tokens = min(int(total_output_tokens * 1.2), max_output)

    input_cost = (total_input_tokens / 1_000_000) * COST_PER_1M_TOKENS[model]["input"]
    output_cost = (total_output_tokens / 1_000_000) * COST_PER_1M_TOKENS[model][
        "output"
    ]
    total_cost = input_cost + output_cost

    return total_cost, {
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
    }


def format_cost_estimate(cost: float, token_counts: Dict[str, int]) -> str:
    """Format the cost estimate and token counts into a human-readable string."""
    return (
        f"Estimated cost: ${cost:.4f}\n"
        f"Input tokens: {token_counts['input_tokens']}\n"
        f"Estimated output tokens: {token_counts['output_tokens']}"
    )
