import os
import openai
import anthropic
import google.generativeai as genai
from dotenv import load_dotenv
import asyncio
import tiktoken
from google.generativeai import GenerativeModel
from config import COST_PER_1M_TOKENS

# Load API keys from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize clients
openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)


def estimate_tokens(text, model):
    if model.startswith(("gpt-", "o1-")):
        # Use tiktoken for OpenAI models
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    elif model.startswith("claude-"):
        # Claude uses GPT-4's tokenizer, so we can use tiktoken with 'gpt-4'
        encoding = tiktoken.encoding_for_model("gpt-4")
        return len(encoding.encode(text))
    elif model == "gemini-1.5-pro":
        # Use Gemini's built-in count_tokens method
        genai_model = GenerativeModel(model)
        return genai_model.count_tokens(text).total_tokens
    else:
        # Fallback to the rough estimation method
        return len(text.split()) * 1.3


def calculate_cost(model, input_text, system_message=""):
    # Estimate input tokens (including system message)
    input_tokens = estimate_tokens(system_message + "\n\n" + input_text, model)

    # Estimate potential response tokens (assume response is similar in length to input)
    estimated_response_tokens = (
        input_tokens * 2
    )  # Keep space for input reproduced in output

    # Add buffer for JSON structure and potential longer responses
    buffer_tokens = 100 + int(input_tokens * 0.1)  # 100 tokens + 10% of input

    total_estimated_output_tokens = estimated_response_tokens + buffer_tokens
    total_estimated_tokens = input_tokens + total_estimated_output_tokens

    # Calculate cost
    input_cost = (input_tokens / 1_000_000) * COST_PER_1M_TOKENS[model]["input"]
    output_cost = (total_estimated_output_tokens / 1_000_000) * COST_PER_1M_TOKENS[
        model
    ]["output"]
    total_cost = input_cost + output_cost

    return (
        total_cost,
        input_tokens,
        total_estimated_output_tokens,
        total_estimated_tokens,
    )


async def get_openai_response(prompt, system_message, model, temperature=0.7):
    if model.startswith("o1-"):
        combined_message = system_message + "\n\n\n" + prompt
        response = await openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": combined_message},
            ],
        )
    else:
        response = await openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
    content = response.choices[0].message.content.strip()
    usage = response.usage
    return content, usage.prompt_tokens, usage.completion_tokens


async def get_claude_response(prompt, system_message):
    full_prompt = f"{system_message}\n\nHuman: {prompt}\n\nAssistant:"
    message = await asyncio.to_thread(
        anthropic_client.messages.create,
        model="claude-3-5-sonnet-20240620",
        max_tokens=8192,
        messages=[{"role": "user", "content": full_prompt}],
    )
    content = message.content[0].text
    input_tokens = estimate_tokens(full_prompt, "claude-3-5-sonnet-20240620")
    output_tokens = estimate_tokens(content, "claude-3-5-sonnet-20240620")
    return content, input_tokens, output_tokens


async def get_gemini_response(prompt, system_message):
    model = genai.GenerativeModel("gemini-1.5-pro")
    full_prompt = f"{system_message}\n\n{prompt}"
    response = await model.generate_content_async(full_prompt)
    content = response.text
    input_tokens = estimate_tokens(full_prompt, "gemini-1.5-pro")
    output_tokens = estimate_tokens(content, "gemini-1.5-pro")
    return content, input_tokens, output_tokens
