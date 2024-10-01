import os
import openai
import anthropic
import google.generativeai as genai
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)


async def get_openai_response(prompt, system_message):
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


async def get_claude_response(prompt, system_message):
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    full_prompt = f"{system_message}\n\nHuman: {prompt}\n\nAssistant:"
    message = await client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1024,
        messages=[{"role": "user", "content": full_prompt}],
    )
    return message.content[0].text


async def get_gemini_response(prompt, system_message):
    model = genai.GenerativeModel("gemini-pro")
    full_prompt = f"{system_message}\n\n{prompt}"
    response = await model.generate_content_async(full_prompt)
    return response.text
