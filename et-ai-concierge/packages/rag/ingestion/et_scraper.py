"""
ET News Scraper - Fetch and parse Economic Times articles for RAG ingestion
Respects robots.txt, rate limits, and filters allowed content categories
"""
import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from typing import List, Dict, Any, Optional
import hashlib
import time
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_URL = "https://economictimes.indiatimes.com"
USER_AGENT = "ET-AI-Concierge/1.0 (+https://et-ai-concierge.local)"
RATE_LIMIT_DELAY = 3  # seconds between requests
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 3

ALLOWED_PATTERNS = [
    "/wealth/",
    "/markets/",
    "/et-learn/",
    "/mf/",  # Mutual funds
    "/stock-analysis/",
]

DISALLOWED_PATTERNS = [
    "/opinions/",
    "/blogs/",
    "/comments/",
    "/primeshow",
    "/login.cms",
]

SITEMAP_URLS = [
    "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-today.xml",
    "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-yesterday.xml",
]


# ─── Robots.txt Checker ───────────────────────────────────────────────────────

_robots_cache = None

def get_robots_parser() -> RobotFileParser:
    """Get and cache the robots.txt parser."""
    global _robots_cache
    if _robots_cache is None:
        _robots_cache = RobotFileParser()
        _robots_cache.set_url(f"{BASE_URL}/robots.txt")
        try:
            _robots_cache.read()
            logger.info(f"✅ Loaded robots.txt from {BASE_URL}/robots.txt")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load robots.txt: {e}. Will proceed with default allow.")
            _robots_cache = None
    return _robots_cache


def is_allowed_url(url: str) -> bool:
    """
    Check if URL is allowed for scraping:
    1. Must match an ALLOWED_PATTERN
    2. Must not match a DISALLOWED_PATTERN
    3. Must not violate robots.txt
    """
    if not url.startswith(BASE_URL):
        return False

    # Check explicit disallow patterns
    for pattern in DISALLOWED_PATTERNS:
        if pattern in url:
            logger.debug(f"❌ URL blocked by disallow pattern: {url}")
            return False

    # Check allowed patterns
    allowed = any(pattern in url for pattern in ALLOWED_PATTERNS)
    if not allowed:
        logger.debug(f"❌ URL not in allowed patterns: {url}")
        return False

    # Check robots.txt
    robots = get_robots_parser()
    if robots and not robots.can_fetch(USER_AGENT, url):
        logger.debug(f"❌ URL blocked by robots.txt: {url}")
        return False

    return True


# ─── Sitemap Parser ───────────────────────────────────────────────────────────

def fetch_sitemaps() -> List[str]:
    """
    Fetch today's and yesterday's article URLs from ET sitemaps.
    Returns a list of article URLs.
    """
    urls = []
    
    for sitemap_url in SITEMAP_URLS:
        try:
            logger.info(f"📡 Fetching sitemap: {sitemap_url}")
            response = requests.get(
                sitemap_url,
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")  # Use html.parser instead of xml
            loc_tags = soup.find_all("loc")

            for tag in loc_tags:
                article_url = tag.text.strip()
                if is_allowed_url(article_url):
                    urls.append(article_url)

            logger.info(f"✅ Extracted {len(urls)} allowed URLs from {sitemap_url}")

        except Exception as e:
            logger.error(f"❌ Error fetching sitemap {sitemap_url}: {e}")

    return urls


# ─── Article Fetcher ──────────────────────────────────────────────────────────

def fetch_article_html(url: str, attempt: int = 1) -> Optional[str]:
    """
    Fetch article HTML with retry logic and rate limiting.
    Returns HTML content or None on failure.
    """
    if attempt > MAX_RETRIES:
        logger.error(f"❌ Max retries exceeded for {url}")
        return None

    try:
        time.sleep(RATE_LIMIT_DELAY)  # Rate limiting

        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code == 429:  # Rate limit
            wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60 sec
            logger.warning(f"⏱️ Rate limited (429). Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
            return fetch_article_html(url, attempt + 1)

        if response.status_code == 403:  # Forbidden
            logger.warning(f"⛔ Forbidden (403): {url}")
            return None

        response.raise_for_status()
        return response.text

    except requests.exceptions.Timeout:
        logger.warning(f"⏱️ Timeout fetching {url} (attempt {attempt}), retrying...")
        return fetch_article_html(url, attempt + 1)

    except requests.exceptions.RequestException as e:
        logger.warning(f"❌ Request failed for {url} (attempt {attempt}): {e}")
        if attempt < MAX_RETRIES:
            return fetch_article_html(url, attempt + 1)
        return None


# ─── Article Content Extractor ────────────────────────────────────────────────

def extract_article_content(html: str, url: str) -> Optional[Dict[str, Any]]:
    """
    Parse article HTML and extract: title, body, publish_date, category, tags.
    Returns normalized article dict or None on failure.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title_tag = soup.find("h1", class_="title") or soup.find("h1") or soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"

        # Extract publish date from meta tags
        date_tag = soup.find("meta", attrs={"property": "article:published_time"})
        publish_date = date_tag.get("content", "") if date_tag else None

        # Extract article body
        article_body = soup.find("div", class_="article_content") or soup.find("article")
        if not article_body:
            logger.warning(f"⚠️ Could not find article body for {url}")
            return None

        body_text = article_body.get_text(separator=" ", strip=True)
        if len(body_text.strip()) < 100:
            logger.warning(f"⚠️ Article body too short for {url}")
            return None

        # Extract category from URL structure
        category = "general"
        if "/wealth/" in url:
            category = "wealth"
        elif "/markets/" in url:
            category = "markets"
        elif "/et-learn/" in url:
            category = "learn"
        elif "/mf/" in url:
            category = "mutualfunds"
        elif "/stock-analysis/" in url:
            category = "stocks"

        # Extract tags from meta or from body
        tags = []
        tag_meta = soup.find("meta", attrs={"name": "keywords"})
        if tag_meta:
            tags = [t.strip() for t in tag_meta.get("content", "").split(",")][:5]

        # Generate content hash for deduplication
        content_hash = hashlib.md5(body_text.encode()).hexdigest()

        article = {
            "url": url,
            "title": title,
            "body": body_text,
            "category": category,
            "publish_date": publish_date,
            "tags": tags,
            "content_hash": content_hash,
            "source": "ET",
            "scraped_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"✅ Extracted: {title[:50]}... from {url}")
        return article

    except Exception as e:
        logger.error(f"❌ Error extracting content from {url}: {e}")
        return None


# ─── Main Scraping Pipeline ───────────────────────────────────────────────────

def scrape_et_articles(max_articles: int = 100) -> List[Dict[str, Any]]:
    """
    Main scraping pipeline:
    1. Fetch sitemaps
    2. Filter allowed URLs
    3. Fetch HTML for each URL
    4. Extract content
    5. Return list of articles (limited by max_articles)
    """
    logger.info(f"🔄 Starting ET article scrape (max: {max_articles} articles)...")

    # Step 1: Get URLs from sitemaps
    urls = fetch_sitemaps()
    logger.info(f"📋 Found {len(urls)} allowed URLs from sitemaps")

    if not urls:
        logger.warning("⚠️ No URLs found. Exiting.")
        return []

    # Step 2: Fetch and parse articles
    articles = []
    for i, url in enumerate(urls[:max_articles], 1):
        logger.info(f"[{i}/{min(len(urls), max_articles)}] Processing {url}")

        html = fetch_article_html(url)
        if not html:
            continue

        article = extract_article_content(html, url)
        if article:
            articles.append(article)

        # Rate limiting
        if i % 10 == 0:
            logger.info(f"📦 Extracted {len(articles)} articles so far...")

    logger.info(f"✅ Scrape complete: {len(articles)} articles extracted")
    return articles


# ─── Test function ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    articles = scrape_et_articles(max_articles=5)
    for article in articles:
        print(f"\n📰 {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   Category: {article['category']}")
        print(f"   Date: {article['publish_date']}")
