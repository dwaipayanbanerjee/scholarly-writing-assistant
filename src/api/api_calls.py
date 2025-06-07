import asyncio
from typing import Tuple

import google.generativeai as genai

from src.api.api_clients import api_clients
from src.utils.cost_tracker import cost_tracker
from src.utils.token_cost_utils import calculate_cost_from_usage, estimate_tokens
from src.config.constants import CLAUDE_MAX_TOKENS, DEFAULT_TEMPERATURE
from src.utils.logger import logger

# ---------------------------------------------------------------------------
# Helper – simple async retry with exponential back-off
# ---------------------------------------------------------------------------


async def _retry(coro, *args, retries: int = 3, timeout: int = 60, backoff: float = 1.5):
    """Run *coro* with retries and an overall timeout per attempt."""

    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return await asyncio.wait_for(coro(*args), timeout=timeout)
        except Exception as exc:  # pragma: no cover – network errors vary
            last_exc = exc
            if attempt == retries:
                logger.error("%s failed after %s attempts: %s", coro.__name__, retries, exc)
                raise
            sleep_for = backoff ** attempt
            logger.warning(
                "Retrying %s in %.1fs (%s/%s)…", coro.__name__, sleep_for, attempt, retries
            )
            await asyncio.sleep(sleep_for)


async def get_openai_response(prompt: str, system_message: str, model: str, temperature: float = DEFAULT_TEMPERATURE) -> Tuple[str, int, int]:
    if model.startswith("o1-"):
        user_message = f"{system_message}\n\n\n {prompt}"
        messages = [
            {"role": "user", "content": user_message},
        ]
    else:
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]

    client = api_clients.get_openai_client()

    async def _call():
        return await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )

    response = await _retry(_call)

    content = response.choices[0].message.content.strip()
    usage = response.usage

    # Calculate and track the actual cost
    actual_cost = calculate_cost_from_usage(
        model, usage.prompt_tokens, usage.completion_tokens
    )
    cost_tracker.add_cost(actual_cost)

    return content, usage.prompt_tokens, usage.completion_tokens

async def get_claude_response(prompt: str, system_message: str, model: str = "claude-3-5-sonnet-latest", temperature: float = DEFAULT_TEMPERATURE) -> Tuple[str, int, int]:
    full_prompt = f"{system_message}\n\n{prompt}\n"
    client = api_clients.get_anthropic_client()
    async def _call():
        return await asyncio.to_thread(
            client.messages.create,
            model=model,
            max_tokens=CLAUDE_MAX_TOKENS,
            temperature=temperature,
            messages=[{"role": "user", "content": full_prompt}],
        )

    message = await _retry(_call)
    content = message.content[0].text
    input_tokens = estimate_tokens(full_prompt, model)
    output_tokens = estimate_tokens(content, model)

    # Calculate and track the actual cost
    actual_cost = calculate_cost_from_usage(
        model, input_tokens, output_tokens
    )
    cost_tracker.add_cost(actual_cost)

    return content, input_tokens, output_tokens

async def get_gemini_response(prompt: str, system_message: str, model_name: str = "gemini-1.5-pro", temperature: float = DEFAULT_TEMPERATURE) -> Tuple[str, int, int]:
    model = genai.GenerativeModel(model_name)
    full_prompt = f"{system_message}\n\n{prompt}"
    generation_config = genai.GenerationConfig(temperature=temperature)
    async def _call():
        return await model.generate_content_async(
            full_prompt, generation_config=generation_config
        )

    response = await _retry(_call)
    content = response.text
    input_tokens = estimate_tokens(full_prompt, model_name)
    output_tokens = estimate_tokens(content, model_name)

    # Calculate and track the actual cost
    actual_cost = calculate_cost_from_usage(
        model_name, input_tokens, output_tokens
    )
    cost_tracker.add_cost(actual_cost)

    return content, input_tokens, output_tokens