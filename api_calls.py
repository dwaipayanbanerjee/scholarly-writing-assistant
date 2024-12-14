import os
import openai
import anthropic
import google.generativeai as genai
from dotenv import load_dotenv
import asyncio
from token_cost_utils import estimate_tokens

from cost_tracker import cost_tracker
from token_cost_utils import calculate_cost_from_usage

# Load API keys from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize clients
openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)

async def get_openai_response(prompt, system_message, model, temperature=0.7):
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

    response = await openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )

    content = response.choices[0].message.content.strip()
    usage = response.usage

    # Calculate and track the actual cost
    actual_cost = calculate_cost_from_usage(
        model, usage.prompt_tokens, usage.completion_tokens
    )
    cost_tracker.add_cost(actual_cost)

    return content, usage.prompt_tokens, usage.completion_tokens

async def get_claude_response(prompt: str, system_message: str):
    full_prompt = f"{system_message}\n\n{prompt}\n"
    message = await asyncio.to_thread(
        anthropic_client.messages.create,
        model="claude-3-5-sonnet-latest",
        max_tokens=8192,
        messages=[{"role": "user", "content": full_prompt}],
    )
    content = message.content[0].text
    input_tokens = estimate_tokens(full_prompt, "claude-3-5-sonnet-latest")
    output_tokens = estimate_tokens(content, "claude-3-5-sonnet-latest")

    # Calculate and track the actual cost
    actual_cost = calculate_cost_from_usage(
        "claude-3-5-sonnet-latest", input_tokens, output_tokens
    )
    cost_tracker.add_cost(actual_cost)

    return content, input_tokens, output_tokens

async def get_gemini_response(prompt: str, system_message: str):
    model = genai.GenerativeModel("gemini-1.5-pro")
    full_prompt = f"{system_message}\n\n{prompt}"
    response = await model.generate_content_async(full_prompt)
    content = response.text
    input_tokens = estimate_tokens(full_prompt, "gemini-1.5-pro")
    output_tokens = estimate_tokens(content, "gemini-1.5-pro")

    # Calculate and track the actual cost
    actual_cost = calculate_cost_from_usage(
        "gemini-1.5-pro", input_tokens, output_tokens
    )
    cost_tracker.add_cost(actual_cost)

    return content, input_tokens, output_tokens