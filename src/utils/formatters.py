# formatters.py
"""
Text formatting and processing utilities for the Writing Assistant application.
"""

import re
from datetime import datetime
from typing import Optional

from src.config.constants import OUTPUT_DATE_FORMAT, OUTPUT_FILE_PREFIX, OUTPUT_FILE_EXTENSION


def remove_footnotes(text: str) -> str:
    """
    Removes footnotes formatted as [number], [roman numeral], (number), or (roman numeral).
    
    Args:
        text: The input text containing footnotes
        
    Returns:
        The text with footnotes removed
    """
    # Remove [number] or [roman numeral] patterns
    text = re.sub(r"\[(?:\d+|[ivx]+)\]", "", text, flags=re.IGNORECASE)
    # Remove (number) or (roman numeral) patterns
    text = re.sub(r"\((?:\d+|[ivx]+)\)", "", text, flags=re.IGNORECASE)
    # Replace multiple spaces or tabs with a single space
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def normalize_line_endings(text: str) -> str:
    """Normalize all line endings to Unix-style (LF)."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def generate_output_filename(timestamp: Optional[datetime] = None) -> str:
    """
    Generate a filename for output files.
    
    Args:
        timestamp: Optional datetime object. If not provided, uses current time.
        
    Returns:
        The formatted filename
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    timestamp_str = timestamp.strftime(OUTPUT_DATE_FORMAT)
    return f"{OUTPUT_FILE_PREFIX}{timestamp_str}{OUTPUT_FILE_EXTENSION}"