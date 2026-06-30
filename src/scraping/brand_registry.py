# src/scraping/brand_registry.py
"""
Brand Registry — known major brands with Wikipedia fallback URLs and
authentic visual identity hints (colors, tone, industry).

When a direct brand website is blocked by Cloudflare / Akamai / CAPTCHA,
the pipeline automatically falls back to the brand's Wikipedia article,
which contains rich factual content about history, products, and market position.

Brand color/tone hints override scraped values so the poster palette
always matches the real brand identity regardless of what Wikipedia's
CSS returns.
"""

from urllib.parse import urlparse

# domain substring → brand config
# Keys must be lowercased and without 'www.'
BRAND_REGISTRY: dict = {
    "nike.com": {
        "name":            "Nike",
        "wikipedia":       "https://en.wikipedia.org/wiki/Nike,_Inc.",
        "primary_color":   "#111111",
        "secondary_color": "#e31837",
        "tone":            "bold",
        "industry":        "Athletic Apparel & Footwear",
        "unsplash_query":  "Nike sneakers running athlete",
    },
    "apple.com": {
        "name":            "Apple",
        "wikipedia":       "https://en.wikipedia.org/wiki/Apple_Inc.",
        "primary_color":   "#1d1d1f",
        "secondary_color": "#0071e3",
        "tone":            "minimal",
        "industry":        "Consumer Electronics & Software",
        "unsplash_query":  "Apple iPhone MacBook product",
    },
    "adidas.com": {
        "name":            "Adidas",
        "wikipedia":       "https://en.wikipedia.org/wiki/Adidas",
        "primary_color":   "#0a0a0a",
        "secondary_color": "#ffffff",
        "tone":            "bold",
        "industry":        "Sportswear & Footwear",
        "unsplash_query":  "Adidas sneakers sport athlete",
    },
    "redbull.com": {
        "name":            "Red Bull",
        "wikipedia":       "https://en.wikipedia.org/wiki/Red_Bull",
        "primary_color":   "#0d0d0d",
        "secondary_color": "#cc1e4a",
        "tone":            "bold",
        "industry":        "Energy Drinks & Extreme Sports",
        "unsplash_query":  "Red Bull extreme sport energy",
    },
    "puma.com": {
        "name":            "Puma",
        "wikipedia":       "https://en.wikipedia.org/wiki/Puma_(brand)",
        "primary_color":   "#0a0a0a",
        "secondary_color": "#ff6600",
        "tone":            "bold",
        "industry":        "Sportswear & Lifestyle",
        "unsplash_query":  "Puma sneakers sport lifestyle",
    },
    "coca-cola.com": {
        "name":            "Coca-Cola",
        "wikipedia":       "https://en.wikipedia.org/wiki/The_Coca-Cola_Company",
        "primary_color":   "#800000",
        "secondary_color": "#f40009",
        "tone":            "friendly",
        "industry":        "Beverages & FMCG",
        "unsplash_query":  "Coca-Cola drink refreshing",
    },
    "spotify.com": {
        "name":            "Spotify",
        "wikipedia":       "https://en.wikipedia.org/wiki/Spotify",
        "primary_color":   "#121212",
        "secondary_color": "#1db954",
        "tone":            "friendly",
        "industry":        "Music Streaming & Audio",
        "unsplash_query":  "music headphones playlist listening",
    },
    "dior.com": {
        "name":            "Dior",
        "wikipedia":       "https://en.wikipedia.org/wiki/Christian_Dior_SE",
        "primary_color":   "#0a0a0a",
        "secondary_color": "#c9a96e",
        "tone":            "premium",
        "industry":        "Luxury Fashion & Beauty",
        "unsplash_query":  "luxury fashion haute couture elegant",
    },
    "tesla.com": {
        "name":            "Tesla",
        "wikipedia":       "https://en.wikipedia.org/wiki/Tesla,_Inc.",
        "primary_color":   "#171a20",
        "secondary_color": "#e82127",
        "tone":            "minimal",
        "industry":        "Electric Vehicles & Clean Energy",
        "unsplash_query":  "Tesla electric car futuristic",
    },
    "samsung.com": {
        "name":            "Samsung",
        "wikipedia":       "https://en.wikipedia.org/wiki/Samsung",
        "primary_color":   "#0a1428",
        "secondary_color": "#1428a0",
        "tone":            "professional",
        "industry":        "Consumer Electronics & Technology",
        "unsplash_query":  "Samsung smartphone technology screen",
    },
}


def lookup(url: str) -> dict | None:
    """
    Returns registry entry for a URL, or None if not a known brand.
    Matches on domain substring — works for www.nike.com, nike.com/products, etc.
    """
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return None
    for brand_domain, data in BRAND_REGISTRY.items():
        if brand_domain in domain:
            return data
    return None


def get_wikipedia_fallback(url: str) -> str:
    """Returns Wikipedia URL for the brand, or empty string if unknown."""
    entry = lookup(url)
    return entry.get("wikipedia", "") if entry else ""


def get_visual_hints(url: str) -> dict:
    """
    Returns authentic brand colors, tone, and Unsplash search query.
    Applied AFTER scraping so they override scraped CSS colors with
    the real brand palette.
    """
    entry = lookup(url)
    if not entry:
        return {}
    return {
        "primary_color":   entry.get("primary_color", ""),
        "secondary_color": entry.get("secondary_color", ""),
        "tone":            entry.get("tone", ""),
        "unsplash_query":  entry.get("unsplash_query", ""),
    }


def get_clean_name(url: str) -> str:
    """Returns clean brand name (e.g. 'Nike' not 'Nike, Inc.')"""
    entry = lookup(url)
    return entry.get("name", "") if entry else ""
