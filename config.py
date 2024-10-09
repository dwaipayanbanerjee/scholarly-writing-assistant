# config.py
MODEL_CHOICES = [
    "o1-mini",
    "o1-preview",
    "gpt-4o",
    "gpt-4o-mini",
    "claude-3-5-sonnet-20240620",
    "gemini-1.5-pro",
]

MAX_OUTPUT_TOKENS = {
    "claude-3-5-sonnet-20240620": 8192,
    "gpt-4o": 16384,
    "gpt-4o-mini": 16384,
    "o1-preview": 32768,
    "o1-mini": 65536,
    "gemini-1.5-pro": 8192,
}

# Cost per 1M tokens
COST_PER_1M_TOKENS = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.150, "output": 0.600},
    "o1-preview": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    "claude-3-5-sonnet-20240620": {"input": 3.00, "output": 15.00},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
}

SYSTEM_MESSAGES = {
    "Writing Assistant": (
        "Review the text for clarity and readability. Simplify overly complex sentences. "
        "Maintain a formal tone, while also ensuring that the style is engaging and not dry or dull. "
        "Take stylistic chances where appropriate. "
        "Preserve the author's unique voice and style while improving the overall flow. "
        "Favor straightforward language and active voice. Make absolutely sure not to lose any details. "
        "When appropriate, use a more conversational tone to avoid stiffness. "
        "Ensure that transitions between ideas are smooth and logical. "
        "Do not shorten when a longer sentence is more stylistically pleasing. "
        "Be judicious and do not feel compelled to make unnecessary changes. "
        'Respond with a JSON object following the schema: {"revisions": [{"original": "...", "revised": "..."}]} '
        "Do not include any Markdown formatting or code blocks. Do not add extraneous text around the JSON object. "
        "Strict Rule: Process ALL the text given to you, do not leave anything out. Take all the time you need. "
    ),
    "Creative Writing Assistant": (
        "Review the text for clarity and readability. Simplify overly complex sentences where possible, but keep an eye for opportunities to add a bit of style. "
        "Maintain a formal tone, yet feel free to inject an engaging, slightly informal touch that makes the writing more relatable. "
        "Preserve the author's unique voice and style, enhancing the overall flow without making it feel forced or artificial. "
        "Prioritize straightforward language, active voice, and an engaging rhythm. Retain all details—no loss of substance allowed. "
        "Aim for smooth, natural transitions between ideas, favoring clarity over academic or overly verbose phrasing. "
        "Strike a balance between conversational and formal tone, keeping the writing inviting yet authoritative. "
        "Avoid rigid wording, and keep sentences longer if it enhances flow and engagement. "
        "Make thoughtful revisions that add genuine value, avoiding unnecessary changes. "
        'Respond with a JSON object following the schema: {"revisions": [{"original": "...", "revised": "..."}]} '
        "Do not include any Markdown formatting or code blocks."
    ),
}
