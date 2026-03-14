"""
OpenAI news scraper.

Scrapes https://openai.com for the top N most recent articles.
Uses sitemap.xml as primary source since /news/ is Cloudflare-protected.
Outputs: url, title, raw_text, date.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

OPENAI_SITEMAP_PAGE_URL = "https://openai.com/sitemap.xml/page/"
OPENAI_NEWS_URL = "https://openai.com/news/"
REQUEST_TIMEOUT_SECONDS = 15

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}


def _clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _slug_to_title(slug: str) -> str:
    """Convert a URL slug like 'gpt-5-2-codex' to 'Gpt 5 2 codex'."""
    return slug.replace("-", " ").strip().capitalize()


# ------------------------------------------------------------------
# Strategy 1: Sitemap (most reliable — not Cloudflare-blocked)
# ------------------------------------------------------------------

def _get_article_urls_from_sitemap(n: int) -> list[dict[str, str]]:
    """
    Fetch OpenAI's sitemap and return the N most recent /index/ article URLs,
    sorted by lastmod date descending.
    """
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    try:
        resp = requests.get(
            OPENAI_SITEMAP_PAGE_URL,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
    except (requests.RequestException, ET.ParseError) as exc:
        logger.warning("Failed to fetch/parse OpenAI sitemap: %s", exc)
        return []

    entries: list[dict[str, str]] = []
    for url_tag in root.findall(".//sm:url", ns):
        loc = url_tag.findtext("sm:loc", default="", namespaces=ns).strip()
        lastmod = url_tag.findtext("sm:lastmod", default="", namespaces=ns).strip()

        if not loc or "/index/" not in loc:
            continue

        slug = loc.rstrip("/").split("/")[-1]
        entries.append({"url": loc, "slug": slug, "lastmod": lastmod})

    entries.sort(key=lambda e: e.get("lastmod", ""), reverse=True)
    return entries[:n]


# ------------------------------------------------------------------
# Strategy 2: HTML scrape of /news/ (fallback if sitemap fails)
# ------------------------------------------------------------------

def _get_article_urls_from_html(n: int) -> list[dict[str, str]]:
    """Try to scrape the /news/ listing page directly."""
    try:
        resp = requests.get(OPENAI_NEWS_URL, headers=_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("OpenAI /news/ page blocked or unavailable: %s", exc)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    articles: list[dict[str, str]] = []
    seen: set[str] = set()

    for link in soup.select("a[href]"):
        href = link.get("href", "").strip()
        if not href:
            continue
        if href.startswith("/"):
            full_url = f"https://openai.com{href}"
        elif href.startswith("https://openai.com/"):
            full_url = href
        else:
            continue

        if not re.search(r"openai\.com/(index|research|blog)/[a-z0-9]", full_url, re.I):
            continue

        canonical = full_url.rstrip("/")
        if canonical in seen:
            continue
        seen.add(canonical)

        slug = canonical.split("/")[-1]
        articles.append({"url": full_url, "slug": slug, "lastmod": ""})
        if len(articles) >= n:
            break

    return articles


# ------------------------------------------------------------------
# Article page fetching
# ------------------------------------------------------------------

def _fetch_article_page(url: str) -> dict[str, str]:
    """
    Fetch a single article page and extract: h1 title, full body text, date.

    OpenAI may block with Cloudflare. If blocked, returns empty strings
    and we fall back to the slug-derived title.
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch article %s: %s", url, exc)
        return {"title": "", "raw_text": "", "date": ""}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Title from <h1>
    h1 = soup.select_one("h1")
    title = _clean_whitespace(h1.get_text(" ", strip=True)) if h1 else ""

    # Date from meta tags or <time>
    date_str = ""
    time_tag = soup.select_one("time[datetime]")
    if time_tag:
        date_str = time_tag.get("datetime", "")
    if not date_str:
        meta_date = soup.select_one("meta[property='article:published_time']")
        if meta_date:
            date_str = meta_date.get("content", "")

    # Full body text
    raw_text = ""
    for selector in ["article", "[data-page-content]", "main", ".ui-rich-text"]:
        container = soup.select_one(selector)
        if container:
            raw_text = _clean_whitespace(container.get_text(" ", strip=True))
            if len(raw_text) > 100:
                break

    return {"title": title, "raw_text": raw_text, "date": date_str}


# ------------------------------------------------------------------
# Main scraper
# ------------------------------------------------------------------

def scrape_openai_news(n: int = 5) -> list[dict[str, Any]]:
    """
    Scrape the top *n* articles from OpenAI.

    Primary strategy: sitemap.xml (not blocked by Cloudflare).
    Fallback: direct /news/ page scrape.

    Returns list of dicts with: url, title, raw_text, date.
    """
    # Try sitemap first, then HTML fallback
    entries = _get_article_urls_from_sitemap(n)
    if not entries:
        logger.info("Sitemap failed, trying /news/ HTML scrape...")
        entries = _get_article_urls_from_html(n)

    if not entries:
        logger.error("Could not extract any OpenAI articles from sitemap or listing page.")
        return []

    results: list[dict[str, Any]] = []
    for entry in entries:
        detail = _fetch_article_page(entry["url"])

        # Use page h1 if available, otherwise derive from slug
        title = detail["title"] or _slug_to_title(entry["slug"])

        # Use lastmod from sitemap if page date not available
        date = detail["date"] or entry.get("lastmod", "")

        results.append(
            {
                "url": entry["url"],
                "title": title,
                "raw_text": detail["raw_text"],
                "date": date,
            }
        )

    return results


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)
    items = scrape_openai_news(n=3)
    for item in items:
        print(f"\n--- {item['title']} ---")
        print(f"URL:  {item['url']}")
        print(f"Date: {item['date']}")
        print(f"Text: {item['raw_text'][:200]}..." if item["raw_text"] else "Text: [blocked by Cloudflare]")
    print(f"\n{json.dumps(items, indent=2, ensure_ascii=False)}")
