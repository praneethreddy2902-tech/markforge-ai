# src/scraping/unsplash_fetcher.py
"""
Unsplash API integration for high-quality brand photography.

Fetches 3 images (main tall + 2 stacked thumbs) for the poster grid.
Attribution is required by Unsplash API guidelines — this module
collects and returns photographer credit data alongside URLs.

API docs: https://unsplash.com/documentation
Free tier: 50 requests/hour, 5 000/month.
"""

import logging
import requests

logger = logging.getLogger(__name__)

_API = "https://api.unsplash.com"

# Words too generic/short to be useful as extra query keywords
_STOP = {
    "the", "a", "an", "is", "are", "was", "for", "and", "or",
    "of", "to", "in", "on", "at", "by", "with", "its", "that",
    "this", "has", "have", "been", "from", "their", "about",
}


def _headers(access_key: str) -> dict:
    return {"Authorization": f"Client-ID {access_key}", "Accept-Version": "v1"}


def _search(query: str, access_key: str, per_page: int = 5) -> list:
    """Raw Unsplash photo search. Returns list of photo result dicts."""
    try:
        resp = requests.get(
            f"{_API}/search/photos",
            params={"query": query, "per_page": per_page, "content_filter": "high"},
            headers=_headers(access_key),
            timeout=8,
        )
        if resp.status_code == 401:
            logger.error("Unsplash: invalid access key — check UNSPLASH_ACCESS_KEY in .env")
            return []
        if resp.status_code == 403:
            logger.warning("Unsplash: rate limit reached or app not approved")
            return []
        if resp.status_code != 200:
            logger.warning(f"Unsplash HTTP {resp.status_code} for '{query}'")
            return []
        return resp.json().get("results", [])
    except Exception as e:
        logger.warning(f"Unsplash search error: {e}")
        return []


def _trigger_download(download_location: str, access_key: str) -> None:
    """
    Required by Unsplash API terms: notify Unsplash when an image is used.
    Fire-and-forget — failure is non-critical.
    """
    try:
        requests.get(download_location, headers=_headers(access_key), timeout=4)
    except Exception:
        pass


def fetch_brand_images(
    brand_name: str,
    description: str = "",
    access_key: str = "",
    count: int = 3,
    custom_query: str = "",
) -> tuple:
    """
    Fetch high-quality Unsplash images for a brand's poster grid.

    Search waterfall — stops as soon as `count` unique photos are found:
      0. custom_query  — brand registry curated query (most targeted)
      1. brand_name    — brand lifestyle & identity shots
      2. brand + product — product photography
      3. description keyword — industry-level fallback

    Args:
        brand_name:   Extracted brand name (e.g. "Nike", "Apple")
        description:  Brand meta description — fallback keyword source
        access_key:   Unsplash API access key
        count:        Number of images (default 3 for poster grid)
        custom_query: Curated query from brand registry (e.g. "Nike sneakers running")

    Returns:
        (urls, credits)
        urls    — list of regular-size image URLs (max 1080 px wide)
        credits — list of {"name": str, "profile": str} for attribution
    """
    if not access_key:
        return [], []

    collected: list = []
    seen_ids: set = set()

    def add(results: list) -> None:
        for photo in results:
            pid = photo.get("id", "")
            if pid and pid not in seen_ids and len(collected) < count:
                seen_ids.add(pid)
                collected.append(photo)

    # 0. Registry curated query — most relevant for known brands
    if custom_query:
        add(_search(custom_query, access_key, per_page=count + 2))

    # 1. Brand name alone
    if len(collected) < count:
        add(_search(brand_name, access_key, per_page=count + 2))

    # 2. Brand + "product"
    if len(collected) < count:
        add(_search(f"{brand_name} product", access_key, per_page=count + 2))

    # 3. Brand + first meaningful noun from meta description
    if len(collected) < count and description:
        keywords = [
            w.strip(".,;:()")
            for w in description.lower().split()
            if len(w) > 3 and w.strip(".,;:()") not in _STOP
        ]
        if keywords:
            add(_search(f"{brand_name} {keywords[0]}", access_key, per_page=count))

    # Extract URLs and attribution; trigger required download notifications
    urls: list = []
    credits: list = []

    for photo in collected:
        url = photo.get("urls", {}).get("regular", "")
        if not url:
            continue

        urls.append(url)
        credits.append({
            "name":    photo.get("user", {}).get("name", "Unknown"),
            "profile": photo.get("user", {}).get("links", {}).get("html", "https://unsplash.com"),
        })

        dl_loc = photo.get("links", {}).get("download_location", "")
        if dl_loc:
            _trigger_download(dl_loc, access_key)

    logger.info(f"Unsplash: {len(urls)}/{count} images fetched for '{brand_name}'")
    return urls, credits
