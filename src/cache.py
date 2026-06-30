"""
src/cache.py
URL brand profile caching — saves pipeline results to disk.
Re-running the same URL loads instantly from cache instead of re-scraping.
Cache expires after 7 days.
"""

import json
import os
import time
import hashlib

import config


CACHE_TTL_SECONDS = 7 * 24 * 3600  # 7 days


def _cache_path(url: str) -> str:
    normalised = url.strip().lower().rstrip("/")
    url_hash = hashlib.md5(normalised.encode()).hexdigest()[:10]
    return os.path.join(config.CACHE_PATH, f"{url_hash}.json")


def save(url: str, brand_assets: dict, parsed_output: dict) -> str:
    """Save brand_assets + parsed_output to disk. Returns file path."""
    os.makedirs(config.CACHE_PATH, exist_ok=True)
    payload = {
        "url":           url,
        "cached_at":     time.time(),
        "brand_assets":  brand_assets,
        "parsed_output": parsed_output,
    }
    path = _cache_path(url)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


def load(url: str, force_refresh: bool = False) -> dict | None:
    """
    Load cached result for a URL.
    Returns dict with {brand_assets, parsed_output} or None if not found/expired.
    """
    if force_refresh:
        return None

    path = _cache_path(url)
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    age = time.time() - payload.get("cached_at", 0)
    if age > CACHE_TTL_SECONDS:
        return None  # Stale

    return {
        "brand_assets":  payload["brand_assets"],
        "parsed_output": payload["parsed_output"],
    }


def exists(url: str) -> bool:
    """Check whether a valid cache entry exists for this URL."""
    return load(url) is not None


def cache_info(url: str) -> dict:
    """Return metadata about the cache entry for a URL."""
    path = _cache_path(url)
    if not os.path.exists(path):
        return {"cached": False}
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        age_seconds = time.time() - payload.get("cached_at", 0)
        return {
            "cached":      True,
            "age_seconds": int(age_seconds),
            "age_human":   _human_age(age_seconds),
            "stale":       age_seconds > CACHE_TTL_SECONDS,
        }
    except Exception:
        return {"cached": False}


def delete(url: str) -> bool:
    """Delete cache for a URL."""
    path = _cache_path(url)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def _human_age(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s ago"
    if seconds < 3600:
        return f"{int(seconds/60)}m ago"
    if seconds < 86400:
        return f"{int(seconds/3600)}h ago"
    return f"{int(seconds/86400)}d ago"