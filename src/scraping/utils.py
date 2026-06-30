# src/scraping/utils.py
"""
Scraping Helper Utilities
--------------------------
URL validation, content checks, and file saving helpers.
"""

import os
import re
import logging
import requests
from urllib.parse import urlparse

import config

logger = logging.getLogger(__name__)


def validate_url(url: str) -> tuple:
    """
    Returns (is_valid, error_message).
    Call this BEFORE scraping anything.
    """
    # Check format
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False, "Invalid URL format. Must start with http:// or https://"

    # Check reachability
    try:
        resp = requests.head(
            url,
            timeout=8,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if resp.status_code == 403:
            return True, "403 detected — Selenium fallback will be used."
            
             
        if resp.status_code == 404:
            return False, "Page not found (404). Check the URL."
        if resp.status_code >= 400:
            return False, f"Server returned error {resp.status_code}."
    except requests.exceptions.Timeout:
        return False, "Request timed out. Site may be slow or down."
    except requests.exceptions.ConnectionError:
        return False, "Cannot reach this URL. Check your internet connection."

    return True, ""


def is_valid_url(url: str) -> bool:
    """
    Simple boolean check — backward compatible with scraper.py.
    """
    is_valid, _ = validate_url(url)
    return is_valid


def extract_domain_name(url: str) -> str:
    """
    Extracts clean domain name as fallback brand name.
    https://www.nike.com/products → 'Nike'
    """
    domain = urlparse(url).netloc
    domain = domain.replace("www.", "").split(".")[0]
    return domain.capitalize()


def check_content_length(text: str, min_words: int = 80) -> tuple:
    """
    Checks if scraped text has enough content to be useful.
    Call this AFTER scraping, BEFORE cleaning.
    """
    word_count = len(text.split())
    if word_count < min_words:
        return False, (
            f"Page has only {word_count} words. "
            f"Needs at least {min_words} for meaningful output."
        )
    return True, ""


def sanitise_filename(url: str) -> str:
    """
    Converts a URL into a safe filename for saving raw data.
    https://example.com/products → example_com_products.txt
    """
    name = re.sub(r"https?://", "", url)
    name = re.sub(r"[^a-zA-Z0-9]", "_", name)
    name = name.strip("_")[:80]
    return f"{name}.txt"


def save_raw_text(text: str, url: str) -> str:
    """
    Saves raw scraped text to data/raw/ for debugging.
    """
    os.makedirs(config.RAW_DATA_PATH, exist_ok=True)
    filename = sanitise_filename(url)
    filepath = os.path.join(config.RAW_DATA_PATH, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

    logger.info(f"Raw text saved → {filepath}")
    return filepath