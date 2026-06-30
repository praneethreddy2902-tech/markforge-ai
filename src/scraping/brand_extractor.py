# src/scraping/brand_extractor.py
"""
Brand Asset Extractor
----------------------
Extracts logo, brand name, colors, tone, description,
and product images from HTML.
No LLM needed — pure HTML parsing.

Changelog (vs previous version):
  - extract_logo: Added Clearbit as Priority 2 (primary for non-Wikipedia pages).
    Previous version was missing Clearbit entirely despite it being listed as
    PRIMARY in Section 8.1 of the handoff doc.
  - extract_product_images: Extended WIKI_SKIP_SUBSTRINGS to filter Wikipedia/
    Wikimedia content URLs (wikipedia, wikimedia, commons, upload.wiki, map,
    portrait). Previous version only caught "flag" and "signature".
  - fetch_unsplash_images: New function — waterfall image search via Unsplash API.
    Tries brand_name → industry → tone until 3 images collected.
    Auto-disabled when UNSPLASH_ACCESS_KEY is not set.
  - extract_product_images: Added og:image:secure_url support (Change 2).
  - extract_product_images: Added data-original and data-image lazy-load
    attribute fallbacks for modern ecommerce sites (Change 3).
  - detect_brand_tone: Added 'witty' tone for food/lifestyle brands (Change 4).
  - extract_product_images: Expanded PRODUCT_SIGNALS with showcase, campaign,
    lifestyle, editorial, collection (Change 1).
"""

import re
import logging
from typing import Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def extract_logo(soup: BeautifulSoup, url: str) -> str:
    """
    Returns the best available logo URL using a prioritised fallback chain.

    Priority order:
    1. Wikipedia infobox logo  (Wikipedia pages only)
    2. Clearbit API            (non-Wikipedia — highest quality, returns clean SVG/PNG)
    3. <img> with "logo"/"wordmark"/"brand-mark" in class, id, alt, or src
    4. apple-touch-icon        (high-res, brand-approved square icon)
    5. PNG/WebP/SVG favicon link tag
    6. Google Favicon Service  (128px — always resolves for any domain)
    """
    domain = urlparse(url).netloc.lower()
    is_wikipedia = "wikipedia.org" in domain

    # ── Priority 1 (Wikipedia only) ──────────────────────────────────────────
    # Brand logo lives in the article infobox table.
    # apple-touch-icon on Wikipedia returns Wikipedia's own "W" icon, not the brand.
    if is_wikipedia:
        infobox = soup.find(class_=lambda c: c and (
            "infobox" in (c if isinstance(c, str) else " ".join(c))
        ))
        if infobox:
            for img in infobox.find_all("img"):
                src = img.get("src", "")
                if not src:
                    continue
                abs_src = _abs(src, url)
                try:
                    w = int(img.get("width", 100) or 100)
                    if w < 40:
                        continue
                except (ValueError, TypeError):
                    pass
                if abs_src and abs_src.startswith("http"):
                    return abs_src

    # ── Priority 2: Clearbit (non-Wikipedia) ─────────────────────────────────
    # Clearbit returns a clean, high-res logo PNG for any known brand by domain.
    # This is the primary strategy for real brand sites — it almost always wins.
    if not is_wikipedia:
        try:
            import tldextract
            ext = tldextract.extract(url)
            if ext.domain and ext.suffix:
                clearbit_url = f"https://logo.clearbit.com/{ext.domain}.{ext.suffix}"
                import requests as _req
                resp = _req.get(clearbit_url, timeout=4)
                if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
                    logger.info(f"Logo: Clearbit hit — {clearbit_url}")
                    return clearbit_url
        except Exception as e:
            logger.debug(f"Clearbit logo lookup failed: {e}")

    # ── Priority 3: <img> with logo signals in attributes ────────────────────
    for img in soup.find_all("img"):
        src = img.get("src", "") or img.get("data-src", "")
        if not src:
            continue
        class_str = " ".join(img.get("class", []))
        signals = " ".join([
            img.get("alt", ""),
            class_str,
            img.get("id", ""),
            src,
        ]).lower()
        if any(kw in signals for kw in ("logo", "wordmark", "brand-mark", "brand_logo")):
            abs_src = _abs(src, url)
            if abs_src and not abs_src.endswith(".ico"):
                return abs_src

    # ── Priority 4: apple-touch-icon (skip Wikipedia — it returns the W icon) ─
    if not is_wikipedia:
        apple = soup.find("link", rel=lambda r: r and "apple-touch-icon" in r)
        if apple and apple.get("href"):
            href = _abs(apple["href"], url)
            if href:
                return href

    # ── Priority 5: PNG/WebP favicon link tag ────────────────────────────────
    for rel in (["icon"], ["shortcut icon"]):
        fav = soup.find("link", rel=rel)
        if fav and fav.get("href"):
            href = fav["href"]
            if any(href.lower().endswith(ext) for ext in (".png", ".webp")):
                return _abs(href, url)

    # ── Priority 6: Google Favicon Service — always resolves, reliable 128px PNG
    try:
        import tldextract
        ext = tldextract.extract(url)
        if ext.domain and ext.suffix:
            return f"https://www.google.com/s2/favicons?domain={ext.domain}.{ext.suffix}&sz=128"
    except Exception:
        pass

    return ""


def extract_brand_name(soup: BeautifulSoup, url: str) -> str:
    """Extracts the most likely brand/company name."""
    # Wikipedia fix: extract article title directly from the page heading
    # og:site_name returns "Wikipedia", og:title returns "Nike, Inc. - Wikipedia"
    # but something upstream is returning "En" — force-extract from <h1 id="firstHeading">
    if "wikipedia.org" in urlparse(url).netloc.lower():
        first_heading = soup.find("h1", id="firstHeading")
        if first_heading and first_heading.text.strip():
            return first_heading.text.strip()

    site_name = soup.find("meta", property="og:site_name")
    if site_name and site_name.get("content"):
        return site_name["content"].strip()

    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
        title = re.split(r"\s*[-|·—]\s*", title)[0].strip()
        if title:
            return title

    title_tag = soup.find("title")
    if title_tag and title_tag.text:
        title = title_tag.text.strip()
        title = re.split(r"\s*[-|·—]\s*", title)[0].strip()
        if title and len(title) < 60:
            return title

    h1 = soup.find("h1")
    if h1 and h1.text.strip():
        return h1.text.strip()[:60]

    domain = urlparse(url).netloc
    domain = domain.replace("www.", "").split(".")[0].capitalize()
    return domain


def extract_brand_colors(html: str) -> list:
    """Extracts hex and rgb color values from HTML/CSS."""
    found = []

    hex_colors = re.findall(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b', html)
    for h in hex_colors:
        if len(h) == 3:
            h = h[0]*2 + h[1]*2 + h[2]*2
        found.append(f"#{h.upper()}")

    rgb_colors = re.findall(
        r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', html
    )
    for r, g, b in rgb_colors:
        found.append('#{:02X}{:02X}{:02X}'.format(int(r), int(g), int(b)))

    def is_brand_color(hex_c: str) -> bool:
        h = hex_c.lstrip("#")
        try:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        except Exception:
            return False
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        saturation = max(r, g, b) - min(r, g, b)
        if brightness > 220 and saturation < 30:
            return False
        if brightness < 25:
            return False
        if saturation < 15:
            return False
        return True

    filtered = [c for c in found if is_brand_color(c)]
    seen, unique = set(), []
    for c in filtered:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    return unique[:5] if unique else ["#1a1a2e", "#e94560", "#ffffff"]


def detect_brand_tone(soup: BeautifulSoup, url: str = "") -> str:
    """
    Detects brand tone using weighted keyword heuristics.

    - Wikipedia pages return 'informational'
    - Multi-word phrases score double
    - Returns 'professional' as default if no keywords match
    """
    from urllib.parse import urlparse

    domain = urlparse(url).netloc.lower().replace("www.", "")
    if "wikipedia.org" in domain:
        return "informational"

    text = soup.get_text(separator=" ").lower()

    tone_keywords = {
        "bold": [
            "athlete", "performance", "sport", "champion", "win",
            "victory", "powerful", "unstoppable", "hustle", "grit",
            "dominate", "fierce", "bold", "daring", "fearless",
            "iconic", "revolutionary", "unleash", "conquer", "beat",
            "just do it", "push limits", "no limits", "born to",
            "built for", "designed to win", "move fast", "just do",
        ],
        "premium": [
            "luxury", "exclusive", "premium", "crafted", "artisan",
            "heritage", "bespoke", "finest", "elite", "prestige",
            "sophisticated", "curated", "unrivalled",
            "world-class", "superior quality",
        ],
        "minimal": [
            "simple", "clean", "minimal", "pure", "essential",
            "focus", "clarity", "seamless", "intuitive", "refined",
            "understated", "effortless", "less is more",
            "distraction-free",
        ],
        "friendly": [
            "community", "together", "everyone", "inclusive",
            "welcoming", "fun", "joyful", "playful", "delight",
            "love", "family", "accessible", "affordable", "happy",
            "for all", "with you",
        ],
        "witty": [
            "craving", "delicious", "yummy", "foodie", "hungry",
            "binge", "obsessed", "addicted", "mood", "vibes",
            "literally", "honestly", "okay but", "wait what",
            "no seriously", "we get it", "food coma",
        ],
        "professional": [
            "enterprise", "solution", "platform", "efficiency",
            "productivity", "optimize", "scalable", "robust",
            "reliable", "compliance", "management", "consulting",
            "expertise", "strategic", "solutions", "business",
        ],
    }

    scores = {tone: 0 for tone in tone_keywords}

    for tone, keywords in tone_keywords.items():
        for keyword in keywords:
            count = text.count(keyword)
            weight = 2 if " " in keyword else 1
            scores[tone] += count * weight

    best_tone = max(scores, key=lambda t: scores[t])
    return best_tone if scores[best_tone] > 0 else "professional"


def extract_product_images(
    soup: BeautifulSoup,
    base_url: str,
    max_images: int = 3
) -> list:
    """
    Extracts up to max_images product/hero images from the page.

    Priority order:
    1. og:image / og:image:secure_url — canonical image set by the site itself
    2. Images with "product", "hero", "feature", "banner" in class/id/alt
    3. Any large image (width >= 200 or no explicit size set)

    Skips SVGs, tracking pixels, icons, and Wikipedia/Wikimedia content images.
    Handles lazy-loaded images via data-src, data-lazy-src, data-original, data-image.
    """
    # Generic noise patterns — apply to all sites
    SKIP_SUBSTRINGS = [
        "pixel", "tracking", "beacon", "spacer", "blank",
        "1x1", "transparent", "flag", "signature",
        "icon", "favicon",
    ]
    # Wikipedia/Wikimedia content URL patterns — these are encyclopedic images,
    # not brand assets.
    WIKI_SKIP_SUBSTRINGS = [
        "wikipedia", "wikimedia", "commons",
        "upload.wiki",          # upload.wikimedia.org CDN
        "/wiki/Special:",       # Wikipedia special pages
        "map",                  # map thumbnails
        "portrait",             # historical portrait photos
    ]
    BUILDING_ALT_TERMS = [
        "campus", "headquarter", "headquarters", "building", "exterior",
        "aerial", "office", "factory", "facility", "hq",
    ]
    # Change 1: expanded with showcase, campaign, lifestyle, editorial, collection
    PRODUCT_SIGNALS = [
        "product", "hero", "feature", "banner", "cover", "main", "primary",
        "showcase", "campaign", "lifestyle", "editorial", "collection",
    ]

    def is_skippable(src: str) -> bool:
        s = src.lower().split("?")[0]
        if s.endswith(".svg"):
            return True
        if any(t in s for t in SKIP_SUBSTRINGS):
            return True
        if any(t in s for t in WIKI_SKIP_SUBSTRINGS):
            return True
        return False

    def is_building_image(img, src: str) -> bool:
        alt = img.get("alt", "").lower()
        src_lower = src.lower()
        return any(t in alt or t in src_lower for t in BUILDING_ALT_TERMS)

    def has_product_signal(img) -> bool:
        class_str = " ".join(img.get("class", []))
        signals = " ".join([
            img.get("alt", ""),
            class_str,
            img.get("id", ""),
            img.get("src", ""),
        ]).lower()
        return any(kw in signals for kw in PRODUCT_SIGNALS)

    collected = []
    seen = set()

    def add(url_str: str):
        if url_str and url_str not in seen and len(collected) < max_images:
            seen.add(url_str)
            collected.append(url_str)

    # Pass 1: og:image and og:image:secure_url — canonical images chosen by the brand.
    # Change 2: added og:image:secure_url support for Indian/ecommerce sites
    for og in soup.find_all("meta", property=lambda p: p in ("og:image", "og:image:secure_url")):
        content = og.get("content", "")
        if not content or is_skippable(content):
            continue
        if any(t in content.lower() for t in BUILDING_ALT_TERMS):
            logger.debug(f"Skipping building og:image: {content[:60]}")
            continue
        abs_url = _abs(content, base_url)
        if abs_url.startswith("http"):
            add(abs_url)

    if len(collected) >= max_images:
        logger.info(f"Product images extracted: {len(collected)} (og:image only)")
        return collected

    # Pass 2: img tags with product/hero signals in attributes
    # Change 3: added data-original and data-image for lazy-loaded modern sites
    for img in soup.find_all("img"):
        src = (
            img.get("src", "")
            or img.get("data-src", "")
            or img.get("data-lazy-src", "")
            or img.get("data-original", "")
            or img.get("data-image", "")
        )
        if not src or is_skippable(src):
            continue
        if is_building_image(img, src):
            continue
        if not has_product_signal(img):
            continue
        try:
            width = int(img.get("width", 0) or 0)
            height = int(img.get("height", 0) or 0)
            if (width > 0 and width < 100) or (height > 0 and height < 100):
                continue
        except (ValueError, TypeError):
            pass
        abs_url = urljoin(base_url, src)
        if abs_url.startswith("http"):
            add(abs_url)
        if len(collected) >= max_images:
            break

    if len(collected) >= max_images:
        logger.info(f"Product images extracted: {len(collected)}")
        return collected

    # Pass 3: any large image (width >= 200 or no explicit size), skip buildings
    # Change 3: added data-original and data-image here too
    for img in soup.find_all("img"):
        src = (
            img.get("src", "")
            or img.get("data-src", "")
            or img.get("data-lazy-src", "")
            or img.get("data-original", "")
            or img.get("data-image", "")
        )
        if not src or is_skippable(src):
            continue
        if is_building_image(img, src):
            continue
        try:
            width = int(img.get("width", 0) or 0)
            height = int(img.get("height", 0) or 0)
            if width > 0 and width < 200:
                continue
            if height > 0 and height < 100:
                continue
        except (ValueError, TypeError):
            pass
        abs_url = urljoin(base_url, src)
        if abs_url.startswith("http"):
            add(abs_url)
        if len(collected) >= max_images:
            break

    logger.info(f"Product images extracted: {len(collected)}")
    return collected


def fetch_unsplash_images(
    brand_name: str,
    industry: str = "",
    tone: str = "modern",
) -> list:
    """
    Waterfall image search via Unsplash API.

    Tries queries in order until 3 images are collected:
      1. brand_name          — most specific, brand lifestyle shots
      2. industry            — if brand has no dedicated shots
      3. tone + "brand"      — broadest fallback

    Returns list of up to 3 "regular" image URLs (~1080px wide).
    Returns [] silently if UNSPLASH_ACCESS_KEY is not set in config,
    so the pipeline degrades gracefully to scraped images.

    Requires config.UNSPLASH_ACCESS_KEY and config.UNSPLASH_PER_PAGE.
    """
    try:
        from config import UNSPLASH_ACCESS_KEY, UNSPLASH_ENABLED, UNSPLASH_PER_PAGE
    except ImportError:
        logger.debug("Unsplash: config import failed — skipping")
        return []

    if not UNSPLASH_ENABLED:
        logger.debug("Unsplash: disabled (UNSPLASH_ACCESS_KEY not set)")
        return []

    import requests as _req

    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    base_url = "https://api.unsplash.com/search/photos"

    # Waterfall: most specific → most general
    industry_query = industry.strip() if industry.strip() else f"{brand_name} product"
    queries = [
        brand_name.strip(),
        industry_query,
        f"{tone} brand lifestyle",
    ]

    collected = []
    seen_urls = set()

    for query in queries:
        if len(collected) >= UNSPLASH_PER_PAGE:
            break
        if not query:
            continue
        try:
            resp = _req.get(
                base_url,
                headers=headers,
                params={
                    "query": query,
                    "per_page": UNSPLASH_PER_PAGE,
                    "orientation": "landscape",
                    "content_filter": "high",
                },
                timeout=5,
            )
            if resp.status_code == 401:
                logger.error("Unsplash: invalid API key — check UNSPLASH_ACCESS_KEY in .env")
                return []
            if resp.status_code == 403:
                logger.error("Unsplash: rate limit or permission denied")
                return []
            if resp.status_code != 200:
                logger.warning(f"Unsplash: unexpected status {resp.status_code} for query '{query}'")
                continue

            results = resp.json().get("results", [])
            logger.info(f"Unsplash: query='{query}' → {len(results)} results")

            for photo in results:
                url = photo.get("urls", {}).get("regular")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    collected.append(url)
                    if len(collected) >= UNSPLASH_PER_PAGE:
                        break

        except Exception as e:
            logger.warning(f"Unsplash: error on query '{query}': {e}")
            continue

    logger.info(f"Unsplash images collected: {len(collected)}")
    return collected[:UNSPLASH_PER_PAGE]


def extract_brand_assets(html: str, url: str) -> dict:
    """
    Master extractor — returns all brand assets in one call.

    Returns:
        {
            brand_name, description, tone,
            logo_url, brand_colors, favicon_url,
            primary_color, secondary_color,
            product_images
        }
    """
    soup = BeautifulSoup(html, "html.parser")

    # Meta description
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if not meta_tag:
        meta_tag = soup.find("meta", property="og:description")
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()

    brand_name     = extract_brand_name(soup, url)
    logo_url       = extract_logo(soup, url)
    brand_colors   = extract_brand_colors(html)
    tone           = detect_brand_tone(soup, url)
    product_images = extract_product_images(soup, url)

    favicon = soup.find("link", rel=lambda r: r and "icon" in r)
    favicon_url = (
        urljoin(url, favicon["href"])
        if favicon and favicon.get("href") else None
    )

    primary_color   = brand_colors[0] if brand_colors else "#1a1a2e"
    secondary_color = brand_colors[1] if len(brand_colors) > 1 else "#e94560"

    assets = {
        "brand_name":      brand_name,
        "description":     meta_desc,
        "tone":            tone,
        "logo_url":        logo_url,
        "brand_colors":    brand_colors,
        "favicon_url":     favicon_url,
        "primary_color":   primary_color,
        "secondary_color": secondary_color,
        "product_images":  product_images,
    }

    logger.info(
        f"Brand assets extracted — name: {brand_name}, "
        f"tone: {tone}, "
        f"logo: {'yes' if logo_url else 'no'}, "
        f"colors: {brand_colors[:3]}, "
        f"images: {len(product_images)}"
    )

    return assets


# ── Image Download Utility ────────────────────────────────────────────────────

def fetch_image_as_base64(image_url: str, timeout: int = 8, max_bytes: int = 2 * 1024 * 1024) -> str:
    """
    Downloads an image and returns a base64 data URI string.

    Using a data URI embeds the image directly in the HTML so it displays
    correctly inside Streamlit's sandboxed iframe regardless of CSP/CORS.

    Returns empty string if the image fails to download or is not an image.
    """
    import base64
    import requests as req

    if not image_url or not image_url.startswith("http"):
        return ""

    try:
        resp = req.get(
            image_url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; MarkForgeBot/1.0)"},
            stream=True,
        )
        if resp.status_code != 200:
            logger.debug(f"Image fetch failed ({resp.status_code}): {image_url}")
            return ""

        content_type = resp.headers.get("content-type", "image/png").split(";")[0].strip()
        if not content_type.startswith("image/"):
            logger.debug(f"Not an image ({content_type}): {image_url}")
            return ""

        content = resp.raw.read(max_bytes, decode_content=True)
        if not content:
            return ""

        data = base64.b64encode(content).decode("utf-8")
        logger.info(f"Image fetched as base64 — {len(content)//1024}KB from {image_url[:60]}")
        return f"data:{content_type};base64,{data}"

    except Exception as e:
        logger.debug(f"Image fetch error for {image_url}: {e}")
        return ""


# ── Internal Helpers ──────────────────────────────────────────────────────────

def _abs(href: str, base_url: str) -> str:
    """Convert relative URL to absolute."""
    if not href:
        return ""
    if href.startswith("//"):
        scheme = urlparse(base_url).scheme
        return f"{scheme}:{href}"
    if href.startswith("http"):
        return href
    return urljoin(base_url, href)


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, requests
    sys.path.insert(0, ".")

    test_url = "https://en.wikipedia.org/wiki/Nike,_Inc."
    print(f"Testing brand extraction on: {test_url}\n")

    headers = {"User-Agent": "Mozilla/5.0 (compatible; MarkForgeBot/1.0)"}
    html    = requests.get(test_url, headers=headers, timeout=10).text
    assets  = extract_brand_assets(html, test_url)

    print(f"Brand Name     : {assets['brand_name']}")
    print(f"Tone           : {assets['tone']}")
    print(f"Description    : {assets['description'][:80]}...")
    print(f"Logo URL       : {assets['logo_url']}")
    print(f"Brand Colors   : {assets['brand_colors']}")
    print(f"Primary        : {assets['primary_color']}")
    print(f"Secondary      : {assets['secondary_color']}")
    print(f"Product Images : {assets['product_images']}")