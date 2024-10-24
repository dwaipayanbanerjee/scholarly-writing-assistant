# config.py

MODEL_CHOICES = [
    "claude-3-5-sonnet-latest",
    "gpt-4o-mini",
    "gpt-4o",
    "o1-mini",
    "o1-preview",
    "gemini-1.5-pro",
    "claude-3-opus-20240229",
]

MAX_OUTPUT_TOKENS = {
    "claude-3-5-sonnet-latest": 8192,
    "gpt-4o": 16384,
    "gpt-4o-mini": 16384,
    "o1-preview": 32768,
    "o1-mini": 65536,
    "gemini-1.5-pro": 8192,
    "claude-3-opus-20240229": 4096,
}

MAX_CONTEXT_WINDOW = {
    "claude-3-5-sonnet-latest": 200000,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "o1-preview": 128000,
    "o1-mini": 128000,
    "gemini-1.5-pro": 2000000,
    "claude-3-opus-20240229": 200000,
}

# Cost per 1M tokens
COST_PER_1M_TOKENS = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.150, "output": 0.600},
    "o1-preview": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    "claude-3-5-sonnet-latest": {"input": 3.00, "output": 15.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
}

SYSTEM_MESSAGES = {
    "recursive": (
        "You are required to improve the clarity and readability of ONLY the last paragraph of the text provided. Ignore all other paragraphs; they are included solely for context. "
        "Your revisions should simplify complex sentences where appropriate while preserving the core details. "
        "Keep the tone formal yet engaging—avoid making the writing too dry. "
        "You may make stylistic changes to enhance flow and readability, but do not deviate from the author's voice or style. "
        "Focus on smooth transitions, active voice, and overall clarity. "
        "Improve the connection between sentences when appropriate. "
        "Pay attention to prosody and rhythm, and ensure that the text is engaging. "
        "Strict Rule: You must ONLY revise the LAST paragraph. Make no changes to any other part of the text. "
        'Your output should be a single JSON object in the following format: {"revisions": ["..."]}. '
        "Do not include any additional text, explanations, markdown, or code formatting. "
        "Your response must be limited to the improved version of the last paragraph enclosed in the JSON object."
    ),
    "non_recursive": (
        "Review the text for clarity and readability. Simplify overly complex sentences. "
        "Maintain a formal tone, while also ensuring that the style is engaging and not dry or dull. "
        "Take stylistic chances where appropriate. Preserve the author's unique voice and style while improving the overall flow. "
        "Favor straightforward language and active voice. Make absolutely sure not to lose any details. "
        "When appropriate, use a more conversational tone to avoid stiffness. "
        "Ensure that transitions between ideas are smooth and logical. Do not shorten when a longer sentence is more stylistically pleasing. "
        "Be judicious and do not feel compelled to make unnecessary changes. "
        'Respond with a JSON object following the schema: {"revisions": ["..."]}. '
        "Do not include any Markdown formatting or code blocks. Do not add extraneous text around the JSON object."
    ),
}
