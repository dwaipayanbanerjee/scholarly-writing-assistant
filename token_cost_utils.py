import tiktoken
import logging
from config import COST_PER_1M_TOKENS, MAX_OUTPUT_TOKENS, SYSTEM_MESSAGES
import anthropic
import google.generativeai as genai
import re

anthropic_client = anthropic.Client()

# Configure logging for token_cost_utils
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
    elif model == "gemini-1.5-pro":

        counting_model = genai.GenerativeModel(model_name=model)
        total_tokens = counting_model.count_tokens(text)
        total_tokens = total_tokens.total_tokens
        return total_tokens
    else:
        raise ValueError(f"Unsupported model: {model}")


def calculate_cost(
    model: str, input_text: str, system_message: str, recursive: bool = False
):
    if model not in COST_PER_1M_TOKENS:
        raise ValueError(f"Cost information not available for model: {model}")

    text = input_text.strip()
    paragraphs = [para.strip() for para in re.split(r"\n+", text) if para.strip()]
    total_cost = 0
    total_input_tokens = 0
    total_output_tokens = 0

    logger.debug(f"Calculating cost for model: {model}, Recursive: {recursive}")
    if recursive:
        cumulative_text = ""
        for i, paragraph in enumerate(paragraphs):
            current_system_message = (
                SYSTEM_MESSAGES["recursive"]
                if i > 0
                else SYSTEM_MESSAGES["non_recursive"]
            )
            cumulative_text += paragraph + "\n\n"

            input_tokens = estimate_tokens(
                current_system_message + "\n\n" + cumulative_text, model
            )
            estimated_output_tokens = estimate_output_tokens(cumulative_text, model)

            input_cost = (input_tokens / 1_000_000) * COST_PER_1M_TOKENS[model]["input"]
            output_cost = (estimated_output_tokens / 1_000_000) * COST_PER_1M_TOKENS[
                model
            ]["output"]

            total_cost += input_cost + output_cost
            total_input_tokens += input_tokens
            total_output_tokens += estimated_output_tokens

            logger.debug(
                f"Paragraph {i+1}: Input Tokens={input_tokens}, Output Tokens={estimated_output_tokens}, "
                f"Input Cost=${input_cost:.6f}, Output Cost=${output_cost:.6f}"
            )
    else:
        input_tokens = estimate_tokens(system_message + "\n\n" + input_text, model)
        estimated_output_tokens = estimate_output_tokens(input_text, model)

        input_cost = (input_tokens / 1_000_000) * COST_PER_1M_TOKENS[model]["input"]
        output_cost = (estimated_output_tokens / 1_000_000) * COST_PER_1M_TOKENS[model][
            "output"
        ]

        total_cost = input_cost + output_cost
        total_input_tokens = input_tokens
        total_output_tokens = estimated_output_tokens

        logger.debug(
            f"Non-recursive: Input Tokens={input_tokens}, Output Tokens={estimated_output_tokens}, "
            f"Input Cost=${input_cost:.6f}, Output Cost=${output_cost:.6f}"
        )

    logger.debug(
        f"Total Cost: ${total_cost:.6f}, Total Input Tokens: {total_input_tokens}, "
        f"Total Output Tokens: {total_output_tokens}"
    )

    return {
        "model": model,
        "recursive": recursive,
        "input_tokens": total_input_tokens,
        "estimated_output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
        "total_cost": total_cost,
    }


def calculate_cost_from_usage(
    model: str, input_tokens: int, output_tokens: int
) -> float:
    """Calculate the actual cost based on token usage."""
    if model not in COST_PER_1M_TOKENS:
        raise ValueError(f"Cost information not available for model: {model}")

    input_cost = (input_tokens / 1_000_000) * COST_PER_1M_TOKENS[model]["input"]
    output_cost = (output_tokens / 1_000_000) * COST_PER_1M_TOKENS[model]["output"]

    logger.debug(
        f"Calculate from usage - Model: {model}, Input Tokens: {input_tokens}, "
        f"Output Tokens: {output_tokens}, Input Cost=${input_cost:.6f}, Output Cost=${output_cost:.6f}"
    )

    return input_cost + output_cost


def estimate_output_tokens(text: str, model: str) -> int:
    """Estimate the number of output tokens based on input text and model, considering the specific JSON output format."""
    input_tokens = estimate_tokens(text, model)

    # Estimate tokens for the JSON structure
    json_structure_tokens = estimate_tokens('{"revisions": [""]}', model)

    # Estimate tokens for the revised text
    # Use a sliding scale: longer inputs are less likely to expand as much
    if input_tokens < 100:
        expansion_factor = 1.2
    elif input_tokens < 500:
        expansion_factor = 1.1
    else:
        expansion_factor = 1.05

    revised_text_tokens = int(input_tokens * expansion_factor)

    # Total estimated output tokens
    estimated_output = json_structure_tokens + revised_text_tokens

    # Add a small buffer for potential variations
    estimated_output = int(estimated_output * 1.05)

    # Respect max tokens for the model
    max_output = MAX_OUTPUT_TOKENS.get(model, float("inf"))
    estimated_output = min(estimated_output, max_output)

    logger.debug(
        f"Estimate Output Tokens - Input Tokens: {input_tokens}, "
        f"Revised Text Tokens: {revised_text_tokens}, Estimated Output Tokens: {estimated_output}"
    )

    return estimated_output
