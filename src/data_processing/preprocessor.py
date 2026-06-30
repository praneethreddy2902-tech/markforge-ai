# src/data_processing/preprocessor.py
"""
Data Preprocessor Module
-------------------------
Structures cleaned text using Pandas and saves to data/processed/.
This bridges the cleaning step and the chunking step.

Document reference:
  §4 : Use of Pandas — structure data for LLM consumption
  §10: data/processed/ — processed data before sending to Claude
"""

import os
import logging

import pandas as pd

import config

logger = logging.getLogger(__name__)


def structure_scraped_data(cleaned_text: str, source_url: str) -> pd.DataFrame:
    """
    Wraps cleaned text into a Pandas DataFrame for structured handling.
    Document reference: §4 — process_scraped_data() with Pandas.

    Why a DataFrame?
    - Consistent structure across multiple URLs
    - Easy to add/filter columns (url, word_count, char_count)
    - Can scale to multiple URLs without changing the pipeline

    Args:
        cleaned_text: Output from cleaner.clean_text()
        source_url:   The URL this text came from

    Returns:
        A single-row DataFrame with columns:
        [source_url, cleaned_text, char_count, word_count]
    """
    word_count = len(cleaned_text.split())
    char_count = len(cleaned_text)

    df = pd.DataFrame([{
        "source_url":   source_url,
        "cleaned_text": cleaned_text,
        "char_count":   char_count,
        "word_count":   word_count,
    }])

    logger.info(
        f"Structured into DataFrame — "
        f"{char_count} chars, {word_count} words"
    )
    return df


def save_processed_data(df: pd.DataFrame, source_url: str) -> str:
    """
    Saves the cleaned text to data/processed/ as a .txt file.
    Document reference: §10 — data/processed/ folder.

    Args:
        df:         DataFrame from structure_scraped_data()
        source_url: Used to generate the filename

    Returns:
        Path to the saved file.
    """
    os.makedirs(config.PROCESSED_DATA_PATH, exist_ok=True)

    # Generate filename from URL
    safe_name = source_url.replace("https://", "").replace("/", "_")
    safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in safe_name)
    safe_name = safe_name[:80]
    filepath = os.path.join(config.PROCESSED_DATA_PATH, f"{safe_name}_cleaned.txt")

    # Save the cleaned text (not the full DataFrame — just the text)
    cleaned_text = df["cleaned_text"].iloc[0]
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(cleaned_text)

    logger.info(f"Processed text saved → {filepath}")
    return filepath


def preprocess(cleaned_text: str, source_url: str) -> pd.DataFrame:
    """
    Master preprocessing function — the only function other modules call.

    Pipeline:
        cleaned_text (from cleaner.py)
          → structure_scraped_data()   [wrap in DataFrame]
          → save_processed_data()      [save to data/processed/]
          → return DataFrame           [ready for chunker.py]

    Args:
        cleaned_text: Output from cleaner.clean_text()
        source_url:   The source URL

    Returns:
        Structured DataFrame ready for chunker.py
    """
    df = structure_scraped_data(cleaned_text, source_url)
    save_processed_data(df, source_url)
    return df


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.abspath("."))

    from src.scraping.scraper import scrape_url
    from src.data_processing.cleaner import clean_text

    test_url = "https://en.wikipedia.org/wiki/Digital_marketing"

    print("Step 1 — Scraping...")
    raw_text = scrape_url(test_url, save_raw=False)

    print("Step 2 — Cleaning...")
    cleaned = clean_text(raw_text)

    print("Step 3 — Preprocessing...")
    df = preprocess(cleaned, test_url)

    print("\n" + "="*50)
    print("PIPELINE TEST RESULT")
    print("="*50)
    print(f"Source URL  : {df['source_url'].iloc[0]}")
    print(f"Characters  : {df['char_count'].iloc[0]}")
    print(f"Words       : {df['word_count'].iloc[0]}")
    print(f"\nFirst 300 chars of cleaned text:")
    print(df['cleaned_text'].iloc[0][:300])
    print(f"\nCheck data/processed/ for saved file.")