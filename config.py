# config.py

MODEL_CHOICES = [
    "claude-3-5-sonnet-latest",
    "gpt-4o-mini",
    "gpt-4o-2024-11-20",
    "o1-mini",
    "o1-preview",
    "gemini-1.5-pro-002",
    "gemini-exp-1206",
]

MAX_OUTPUT_TOKENS = {
    "claude-3-5-sonnet-latest": 8192,
    "gpt-4o-2024-11-20": 16384,
    "gpt-4o-mini": 16384,
    "o1-preview": 32768,
    "o1-mini": 65536,
    "gemini-1.5-pro-002": 8192,
    "gemini-exp-1206": 8192,
}

MAX_CONTEXT_WINDOW = {
    "claude-3-5-sonnet-latest": 200000,
    "gpt-4o-2024-11-20": 128000,
    "gpt-4o-mini": 128000,
    "o1-preview": 128000,
    "o1-mini": 128000,
    "gemini-1.5-pro-002": 2000000,
    "gemini-exp-1206": 2000000,
}

# Cost per 1M tokens
COST_PER_1M_TOKENS = {
    "gpt-4o-2024-11-20": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.150, "output": 0.600},
    "o1-preview": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    "claude-3-5-sonnet-latest": {"input": 3.00, "output": 15.00},
    "gemini-1.5-pro-002": {"input": 2.50, "output": 10.00},
    "gemini-exp-1206": {"input": 2.50, "output": 10.00},
}

SYSTEM_MESSAGE = """You are an expert writing assistant tasked with improving text clarity and readability. Your role is to enhance any provided text while preserving its core message and style.

Follow these precise instructions:

1. Analysis:
   - Review the text's structure, style, and content
   - Identify areas needing improvement in clarity and flow
   - Note the author's voice and tone

2. Clarity Improvements:
   - Simplify overly complex sentences
   - Break down convoluted passages into digestible segments
   - Use active voice when it enhances clarity
   - Take calculated risks to improve readability
   - Take stylistic liberties to enhance engagement

3. Style Enhancement:
   - Maintain the formal tone while making the text engaging
   - Preserve the author's unique voice and writing style
   - Take calculated stylistic risks to improve narrative flow
   - Vary sentence rhythm and flow
   - Keep longer sentences when they serve the style better

4. Flow and Transitions:
   - Ensure smooth logical progression between ideas
   - Add or improve transitions where needed
   - Maintain coherence throughout the text

5. Content Preservation:
   - Retain all original information and details
   - Ensure revisions maintain the original meaning

6. Output Format:
   - Return the improved text directly, maintaining proper paragraph structure
   - Preserve all meaningful line breaks
   - Do not add any formatting markers"""

USER_MESSAGE_TEMPLATE = """<text_to_revise>
{text}
</text_to_revise>

Please revise this text according to the provided instructions."""