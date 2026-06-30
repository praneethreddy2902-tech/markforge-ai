# src/scraping/official_scraper.py
"""
Official Brand Website Scraper
--------------------------------
Extracts real marketing language from official brand websites.
Targets hero copy, CTAs, slogans, nav categories, product descriptions,
and meta content — the kind of language that makes RAG output brand-authentic.

Falls back gracefully if the site blocks or lacks sufficient content.
The pipeline imports this and uses it BEFORE the standard BeautifulSoup scraper.
If this fails for any reason, the pipeline continues normally with no disruption.
"""

import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# CSS class/id keywords that signal marketing sections
HERO_SIGNALS = [
    "hero", "banner", "masthead", "jumbotron", "splash",
    "headline", "above-fold", "featured", "showcase",
]
CTA_SIGNALS = [
    "cta", "call-to-action", "btn", "button", "shop-now",
    "get-started", "buy-now", "try-free", "learn-more",
]
PRODUCT_SIGNALS = [
    "product", "collection", "catalog", "item",
    "merchandise", "shop", "store",
]
CAMPAIGN_SIGNALS = [
    "campaign", "promotion", "promo", "offer",
    "deal", "feature", "spotlight", "editorial",
]


def fetch_official_page(url: str, timeout: int = 12):
    """
    Fetches HTML from an official brand site.
    Returns (html_content, error_message).
    error_message is None on success.
    """
    try:
        resp = requests.get(
            url,
            headers=BROWSER_HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )
        if resp.status_code == 403:
            return None, f"403 Forbidden — {url} blocks automated access"
        if resp.status_code == 404:
            return None, f"404 Not Found — {url}"
        if resp.status_code >= 500:
            return None, f"Server error {resp.status_code} at {url}"
        resp.raise_for_status()
        return resp.text, None
    except requests.exceptions.Timeout:
        return None, f"Timeout fetching {url}"
    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {e}"


def _has_signal(element, signals: list) -> bool:
    """Check if a BS4 element has any marketing signal in class/id."""
    attrs = []
    for attr in ["class", "id", "data-section", "data-component"]:
        val = element.get(attr, "")
        if isinstance(val, list):
            attrs.extend(val)
        elif val:
            attrs.append(val)
    combined = " ".join(attrs).lower()
    return any(sig in combined for sig in signals)


def extract_hero_text(soup: BeautifulSoup) -> list:
    """
    Extract hero section text: headlines, subheadlines, slogans.
    These are the most brand-authentic pieces of copy on any website.
    """
    hero_texts = []

    # Strategy 1: elements with hero/banner signals in class/id
    for tag in soup.find_all(["section", "div", "header", "article"]):
        if _has_signal(tag, HERO_SIGNALS):
            for text_tag in tag.find_all(["h1", "h2", "h3", "p", "span"]):
                text = text_tag.get_text(strip=True)
                if 15 < len(text) < 300:
                    hero_texts.append(text)

    # Strategy 2: H1 tags are the main brand headline — always include
    for h1 in soup.find_all("h1"):
        text = h1.get_text(strip=True)
        if len(text) > 5 and text not in hero_texts:
            hero_texts.insert(0, text)  # H1 gets top priority

    # Deduplicate preserving order
    seen = set()
    unique = []
    for t in hero_texts:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return unique[:15]


def extract_cta_text(soup: BeautifulSoup) -> list:
    """
    Extract CTA button text and action-oriented copy.
    CTAs are pure brand voice — short, direct, emotionally charged.
    """
    cta_texts = []

    # Elements with CTA signals in class/id
    for tag in soup.find_all(["a", "button"]):
        if _has_signal(tag, CTA_SIGNALS):
            text = tag.get_text(strip=True)
            if 5 < len(text) < 60:
                cta_texts.append(text)

    # Short action-verb text in links/buttons
    action_verbs = [
        "shop", "buy", "get", "try", "start", "discover",
        "explore", "join", "sign up", "learn", "find", "build",
        "create", "launch", "see",
    ]
    for tag in soup.find_all(["a", "button", "span"]):
        text = tag.get_text(strip=True)
        text_lower = text.lower()
        if any(text_lower.startswith(v) for v in action_verbs) and len(text) < 50:
            if text not in cta_texts:
                cta_texts.append(text)

    # Deduplicate
    seen = set()
    unique = []
    for t in cta_texts:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return unique[:10]


def extract_nav_categories(soup: BeautifulSoup) -> list:
    """
    Extract navigation menu items.
    Nav items reveal a brand's product taxonomy and priorities.
    """
    nav_items = []
    for nav in soup.find_all("nav"):
        for link in nav.find_all("a"):
            text = link.get_text(strip=True)
            if 3 < len(text) < 40 and not text.startswith("http"):
                nav_items.append(text)

    # Deduplicate
    seen = set()
    unique = []
    for t in nav_items:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return unique[:20]


def extract_product_descriptions(soup: BeautifulSoup) -> list:
    """
    Extract product and campaign descriptions.
    These contain the brand's actual selling language.
    """
    descriptions = []
    for tag in soup.find_all(["section", "div", "article"]):
        if _has_signal(tag, PRODUCT_SIGNALS + CAMPAIGN_SIGNALS):
            for p_tag in tag.find_all("p"):
                text = p_tag.get_text(strip=True)
                if 30 < len(text) < 500:
                    descriptions.append(text)

    # Deduplicate
    seen = set()
    unique = []
    for t in descriptions:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return unique[:20]


def extract_meta_content(soup: BeautifulSoup) -> dict:
    """
    Extract meta description, og:title, og:description, og:image.
    These are the brand's own curated one-liners — high signal for RAG.
    """
    meta = {}

    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        meta["og_description"] = og_desc["content"].strip()

    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        meta["og_title"] = og_title["content"].strip()

    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        meta["og_image"] = og_image["content"].strip()

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        meta["meta_description"] = meta_desc["content"].strip()

    return meta


def scrape_official_brand_site(url: str, timeout: int = 12) -> dict:
    """
    Master function — scrapes an official brand site and returns structured
    marketing content ready for the RAG pipeline.

    Returns:
    {
        'success':              bool,
        'error':                str | None,
        'marketing_text':       str,   # assembled text for RAG — feed into raw_text
        'hero_texts':           list,
        'cta_texts':            list,
        'nav_categories':       list,
        'product_descriptions': list,
        'meta':                 dict,
        'word_count':           int,
        'source_type':          'official'
    }

    On failure returns success=False with error message.
    Pipeline handles this gracefully — falls through to standard scraper.
    """
    html, error = fetch_official_page(url, timeout=timeout)
    if error:
        return {
            "success":              False,
            "error":                error,
            "marketing_text":       "",
            "hero_texts":           [],
            "cta_texts":            [],
            "nav_categories":       [],
            "product_descriptions": [],
            "meta":                 {},
            "word_count":           0,
            "source_type":          "official",
        }

    soup = BeautifulSoup(html, "html.parser")

    # Remove noise — scripts, styles, forms don't contain brand copy
    for tag in soup(["script", "style", "noscript", "iframe", "svg", "form"]):
        tag.decompose()

    # Extract all marketing sections
    hero_texts           = extract_hero_text(soup)
    cta_texts            = extract_cta_text(soup)
    nav_categories       = extract_nav_categories(soup)
    product_descriptions = extract_product_descriptions(soup)
    meta                 = extract_meta_content(soup)

    # Assemble marketing_text for RAG pipeline.
    # Sections are labelled so embeddings capture the context of each piece.
    # Label format matches the chunk enrichment prefix style already in your pipeline.
    sections = []

    if meta.get("og_title"):
        sections.append(f"Brand Title: {meta['og_title']}")

    if meta.get("og_description"):
        sections.append(f"Brand Description: {meta['og_description']}")

    if meta.get("meta_description"):
        sections.append(f"Brand Summary: {meta['meta_description']}")

    if hero_texts:
        sections.append("Hero Copy:\n" + "\n".join(hero_texts))

    if cta_texts:
        sections.append("Call to Action: " + " | ".join(cta_texts))

    if nav_categories:
        sections.append("Product Categories: " + ", ".join(nav_categories))

    if product_descriptions:
        sections.append("Product Features:\n" + "\n".join(product_descriptions))

    marketing_text = "\n\n".join(sections)
    word_count = len(marketing_text.split())

    logger.info(
        f"Official scrape: {url} | {word_count} words | "
        f"{len(hero_texts)} hero sections | "
        f"{len(cta_texts)} CTAs | "
        f"{len(nav_categories)} nav items"
    )

    return {
        "success":              True,
        "error":                None,
        "marketing_text":       marketing_text,
        "hero_texts":           hero_texts,
        "cta_texts":            cta_texts,
        "nav_categories":       nav_categories,
        "product_descriptions": product_descriptions,
        "meta":                 meta,
        "word_count":           word_count,
        "source_type":          "official",
    }


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://anthropic.com"
    print(f"\nTesting official scraper on: {test_url}")
    print("-" * 60)

    result = scrape_official_brand_site(test_url)

    if result["success"]:
        print(f"Word count     : {result['word_count']}")
        print(f"Hero sections  : {len(result['hero_texts'])}")
        print(f"CTAs           : {len(result['cta_texts'])}")
        print(f"Nav items      : {len(result['nav_categories'])}")
        print(f"\nHero texts preview:")
        for t in result["hero_texts"][:3]:
            print(f"  → {t}")
        print(f"\nCTAs:")
        for t in result["cta_texts"][:5]:
            print(f"  → {t}")
        print(f"\nMarketing text preview (first 400 chars):")
        print(result["marketing_text"][:400])
    else:
        print(f"Failed: {result['error']}")