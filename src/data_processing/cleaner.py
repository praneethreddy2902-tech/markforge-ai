# src/data_processing/cleaner.py
"""
Data Cleaning Module
---------------------
Deep cleans raw scraped text before it enters the RAG pipeline.
This is Step 2 of the pipeline: Data Pre-processing.

Document reference:
  §4 : Clean and Structure Scraped Data
       - Remove noise
       - Normalize whitespace
       - Handle encoding
       - Validation
"""

import re
import logging
import unicodedata

logger = logging.getLogger(__name__)


def remove_noise(text: str) -> str:
    """
    Removes common web noise patterns from raw scraped text.
    Document reference: §4 — Remove Noise.
    """
    # Remove URLs
    text = re.sub(r"http[s]?://\S+", "", text)

    # Remove email addresses
    text = re.sub(r"\S+@\S+\.\S+", "", text)

    # Remove citation markers like [1], [23], [citation needed]
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\[citation needed\]", "", text, flags=re.IGNORECASE)

    # Remove lines that are just numbers (page numbers, IDs)
    text = re.sub(r"\b\d+\b", "", text)

    # Remove excessive repeated punctuation (!!!! or ????)
    text = re.sub(r"[!?]{2,}", ".", text)

    # Remove Wikipedia UI noise
    wiki_noise_patterns = [
        r"Jump to content",
        r"Jump to navigation",
        r"From Wikipedia, the free encyclopedia",
        r"Learn how and when to remove these? messages?",
        r"Please help improve it.*?\.",
        r"Please help update this article.*?\.",
        r"This article has multiple issues.*?\.",
        r"This article is written like.*?\.",
        r"This article needs to be updated.*?\.",
        r"Articles with unsourced statements.*",
        r"articles needing page number citations.*",
        r"Advertising revenue over time.*?\.",
        r"\( August \)|\( February \)|\( March \)|\( June \)",
        r"Digital marketing - Wikipedia",
        r"Add topic",
        r"graph from",
        r"talk page",
    ]
    for pattern in wiki_noise_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    return text


def normalise_whitespace(text: str) -> str:
    """
    Normalises all whitespace to single spaces.
    Document reference: §4 — Normalize Whitespace.
    """
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def handle_encoding(text: str) -> str:
    """
    Ensures consistent UTF-8 compatible text.
    Document reference: §4 — Handle Encoding.
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text


def validate_text(text: str, min_length: int = 100) -> bool:
    """
    Validates that the cleaned text has enough content to be useful.
    Document reference: §4 — Validation.
    """
    if not text or len(text.strip()) < min_length:
        logger.warning(
            f"Text too short after cleaning — "
            f"{len(text)} chars (minimum: {min_length}). "
            f"The URL may have returned a login page or empty content."
        )
        return False
    return True


def clean_text(raw_text: str) -> str:
    """
    Master cleaning function — runs all steps in the correct order.
    This is the only function other modules should call.

    Pipeline (§4):
        raw_text
          → remove_noise()
          → normalise_whitespace()
          → handle_encoding()
          → validate_text()
          → cleaned_text
    """
    logger.info(f"Cleaning text — input: {len(raw_text)} chars")

    text = remove_noise(raw_text)
    text = normalise_whitespace(text)
    text = handle_encoding(text)

    if not validate_text(text):
        raise ValueError(
            "Cleaned text is too short. "
            "The page may be empty, paywalled, or login-protected."
        )

    logger.info(f"Cleaning complete — output: {len(text)} chars")
    return text