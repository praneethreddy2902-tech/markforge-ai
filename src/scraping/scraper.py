# src/scraping/scraper.py
"""
Web Scraper Module
-------------------
Fetches a URL and extracts clean plain text.

Fetch strategy (in order):
  1. requests with realistic browser headers — fast, works on most sites
  2. undetected-chromedriver — patches ChromeDriver to bypass bot detection
     (Cloudflare, basic Akamai, JS-rendered sites)
  3. Plain Selenium — last resort fallback

Note: Heavily protected sites (Nike Akamai, Apple CDN) may still block all
headless approaches. For those, a paid scraping proxy (ScraperAPI, Bright Data)
is the only reliable option.
"""

import logging
import re
import time
import requests
from bs4 import BeautifulSoup

from src.scraping.utils import is_valid_url, save_raw_text

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15
UC_WAIT         = 12   # seconds for JS to finish rendering

# Realistic Chrome browser headers — reduces 403s on many sites
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

NOISE_TAGS = [
    "script", "style", "nav", "footer", "header",
    "aside", "form", "button", "iframe", "noscript",
]

MIN_CONTENT_CHARS = 1500   # if response is shorter, assume it's a challenge page


# ── undetected-chromedriver fetch ─────────────────────────────────────────────

def _fetch_with_uc(url: str) -> str:
    """
    Fetches using undetected-chromedriver — patches ChromeDriver to bypass
    most bot detection (Cloudflare turnstile, basic Akamai, JS challenges).

    Install: pip install undetected-chromedriver
    """
    try:
        import undetected_chromedriver as uc
    except ImportError:
        raise ImportError(
            "undetected-chromedriver not installed. "
            "Run: pip install undetected-chromedriver"
        )

    logger.info(f"undetected-chromedriver: launching for {url}")

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US,en")
    # Do NOT add --headless here — undetected-chromedriver works in
    # headless=True mode passed to Chrome() constructor which is less detectable

    # Auto-detect installed Chrome version so driver and browser match
    import subprocess, re as _re
    try:
        out = subprocess.check_output(
            ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
            stderr=subprocess.DEVNULL
        ).decode()
        ver = int(_re.search(r"(\d+)\.", out).group(1))
    except Exception:
        ver = None
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(options=options, headless=True, use_subprocess=False, version_main=ver)

    try:
        driver.get(url)
        # Initial wait for JS framework to boot
        time.sleep(UC_WAIT)

        # Scroll to trigger lazy-loaded content
        for pct in [0.3, 0.6, 1.0]:
            driver.execute_script(
                f"window.scrollTo(0, document.body.scrollHeight * {pct});"
            )
            time.sleep(1.5)

        # Scroll back to top so og:image and header content is in viewport
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        html = driver.page_source
        logger.info(
            f"undetected-chromedriver fetched — {len(html)} chars, "
            f"title: '{driver.title[:60]}'"
        )
        return html
    finally:
        try:
            driver.quit()
        except Exception:
            pass


# ── Plain Selenium fallback ───────────────────────────────────────────────────

def _fetch_with_selenium(url: str) -> str:
    """
    Basic Selenium fallback — used only if undetected-chromedriver is not
    installed. Detected by most enterprise bot protection.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        raise ConnectionError(
            "Neither undetected-chromedriver nor selenium is installed.\n"
            "Run: pip install undetected-chromedriver"
        )

    logger.info(f"Selenium fallback: launching headless Chrome for {url}")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={REQUEST_HEADERS['User-Agent']}")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    try:
        driver.get(url)
        time.sleep(6)
        html = driver.page_source
        logger.info(f"Selenium fetched — {len(html)} chars")
        return html
    finally:
        driver.quit()


def _use_headless_browser(url: str) -> str:
    """Try undetected-chromedriver first, fall back to plain Selenium."""
    try:
        return _fetch_with_uc(url)
    except ImportError:
        logger.warning("undetected-chromedriver not available, trying plain Selenium")
        return _fetch_with_selenium(url)


# ── Primary Fetch ─────────────────────────────────────────────────────────────

def fetch_page(url: str) -> str:
    """
    Fetches the raw HTML content of a URL.

    Strategy:
      1. requests with full browser headers.
      2. If 403 or response looks like a bot challenge → headless browser.
      3. Headless: undetected-chromedriver → plain Selenium.

    Raises:
        ValueError:      Invalid URL.
        ConnectionError: Page unreachable by any method.
    """
    if not is_valid_url(url):
        raise ValueError(f"Invalid URL: '{url}'")

    logger.info(f"Fetching: {url}")

    try:
        response = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        if response.status_code == 403:
            logger.warning(f"403 on {url} — switching to headless browser")
            return _use_headless_browser(url)

        response.raise_for_status()

        # Some sites return 200 but serve a JS challenge page (Cloudflare)
        # Detect this by checking for very short or challenge-like content
        html = response.text
        if len(html) < MIN_CONTENT_CHARS or _looks_like_challenge(html):
            logger.warning(
                f"Challenge page detected at {url} ({len(html)} chars) "
                f"— switching to headless browser"
            )
            return _use_headless_browser(url)

        logger.info(f"Fetched via requests — {len(html)} chars")
        return html

    except requests.exceptions.Timeout:
        raise ConnectionError(f"Timed out after {REQUEST_TIMEOUT}s: {url}")
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else 0
        if status == 403:
            return _use_headless_browser(url)
        raise ConnectionError(f"HTTP {status}: {url}")
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Request failed: {e}")


def _looks_like_challenge(html: str) -> bool:
    """Heuristic: returns True if the HTML looks like a bot-challenge page."""
    lower = html.lower()
    challenge_signals = [
        "cf-browser-verification",
        "checking your browser",
        "enable javascript",
        "ddos-guard",
        "just a moment",           # Cloudflare "Just a moment..."
        "challenge-form",
        "ray id",                  # Cloudflare Ray ID footer
        "_cf_chl",                 # Cloudflare challenge token
    ]
    return sum(s in lower for s in challenge_signals) >= 2


# ── Text Extraction ───────────────────────────────────────────────────────────

def extract_text(html: str) -> str:
    """
    Extracts clean, meaningful text from HTML.
    Keeps headings and paragraphs — removes nav, footer, scripts, etc.
    """
    soup = BeautifulSoup(html, "html.parser")

    for tag in NOISE_TAGS:
        for element in soup.find_all(tag):
            element.decompose()

    for element in soup.find_all(["table", "sup", "span"]):
        element.decompose()

    meaningful_tags = ["h1", "h2", "h3", "h4", "p", "li", "span", "a"]
    texts = []
    for tag in soup.find_all(meaningful_tags):
        text = tag.get_text(separator=" ").strip()
        # Lower threshold for span/a tags — CTAs are short but valuable
        min_len = 10 if tag.name in ("span", "a") else 30
        if len(text) > min_len and len(text) < 500:
            texts.append(text)

    combined = " ".join(texts)
    combined = re.sub(r"\s+", " ", combined).strip()

    if len(combined) > 50000:
        combined = combined[:50000]
        logger.info("Text truncated to 50,000 chars")

    logger.info(f"Text extracted — {len(combined)} characters")
    return combined


# ── Full Pipeline ─────────────────────────────────────────────────────────────

def scrape_url(url: str, save_raw: bool = True) -> str:
    html = fetch_page(url)
    text = extract_text(html)
    if save_raw:
        save_raw_text(text, url)
    return text


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.nike.com"
    print(f"\nScraping: {test_url}")
    print("-" * 60)
    try:
        text = scrape_url(test_url, save_raw=False)
        print(f"Characters: {len(text)}")
        print(f"Words:      {len(text.split())}")
        print(f"\nPreview:\n{text[:400]}")
    except Exception as e:
        print(f"Error: {e}")
