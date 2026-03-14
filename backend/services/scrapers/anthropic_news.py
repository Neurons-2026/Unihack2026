"""
Anthropic news scraper.

Scrapes https://www.anthropic.com/news for the top N most recent articles.
Outputs: url, title, raw_text, date.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

ANTHROPIC_NEWS_URL = "https://www.anthropic.com/news"
REQUEST_TIMEOUT_SECONDS = 15

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_HEADERS = {"User-Agent": USER_AGENT}


def _clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_listing_links(soup: BeautifulSoup, n: int) -> list[dict[str, str]]:
    """
    Parse the /news listing page for the top n article links.

    Extracts the real title from <h2>/<h4> headings inside the link,
    NOT the category label like "Announcements".
    """
    articles: list[dict[str, str]] = []
    seen: set[str] = set()

    for link in soup.select("a[href]"):
        href = link.get("href", "").strip()
        if not href:
            continue

        # Build full URL
        if href.startswith("/news/") and href != "/news/":
            full_url = f"https://www.anthropic.com{href}"
        elif href.startswith("https://www.anthropic.com/news/") and href.rstrip("/") != ANTHROPIC_NEWS_URL:
            full_url = href
        else:
            continue

        canonical = full_url.rstrip("/")
        if canonical in seen:
            continue
        seen.add(canonical)

        # Extract the REAL title from heading tags, not category labels
        title = ""
        for heading in link.select("h1, h2, h3, h4, h5"):
            candidate = _clean_whitespace(heading.get_text(" ", strip=True))
            # Skip category labels like "Announcements", "Product", "Research"
            if candidate and len(candidate) > 10:
                title = candidate
                break

        # Fallback: if no heading found, try the full link text minus date/category
        if not title:
            full_text = _clean_whitespace(link.get_text(" ", strip=True))
            # Remove date patterns and common category labels
            cleaned = re.sub(r"(Announcements|Product|Research|Policy)\s*", "", full_text)
            cleaned = re.sub(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\s*", "", cleaned)
            title = _clean_whitespace(cleaned)

        if not title or len(title) < 5:
            continue

        articles.append({"url": full_url, "title": title})
        if len(articles) >= n:
            break

    return articles


def _fetch_article_page(url: str) -> dict[str, str]:
    """
    Fetch a single article page and extract the h1 title, full body text, and date.
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

    # Date — look in the article body text for a date pattern
    date_str = ""
    # Try meta tag first
    meta_date = soup.select_one("meta[property='article:published_time']")
    if meta_date:
        date_str = meta_date.get("content", "")

    # Fallback: parse date from the article text (e.g. "Feb 17, 2026")
    if not date_str:
        article_tag = soup.select_one("article") or soup.select_one("main")
        if article_tag:
            text_block = article_tag.get_text(" ", strip=True)[:500]
            date_match = re.search(
                r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}",
                text_block,
            )
            if date_match:
                date_str = date_match.group(0)

    # Full body text from <article>
    raw_text = ""
    article_tag = soup.select_one("article")
    if article_tag:
        raw_text = _clean_whitespace(article_tag.get_text(" ", strip=True))
    else:
        main_tag = soup.select_one("main")
        if main_tag:
            raw_text = _clean_whitespace(main_tag.get_text(" ", strip=True))

    return {"title": title, "raw_text": raw_text, "date": date_str}


def scrape_anthropic_news(n: int = 5) -> list[dict[str, Any]]:
    """
    Scrape the top *n* articles from https://www.anthropic.com/news.

    Returns list of dicts with: url, title, raw_text, date.
    """
    try:
        resp = requests.get(ANTHROPIC_NEWS_URL, headers=_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to fetch Anthropic news listing: %s", exc)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    article_links = _extract_listing_links(soup, n)

    if not article_links:
        logger.warning("No article links found on Anthropic news page — DOM may have changed.")
        return []

    results: list[dict[str, Any]] = []
    for article in article_links:
        detail = _fetch_article_page(article["url"])

        # Prefer the h1 title from the article page over the listing title
        title = detail["title"] or article["title"]

        results.append(
            {
                "url": article["url"],
                "title": title,
                "raw_text": detail["raw_text"],
                "date": detail["date"],
            }
        )

    return results


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)
    items = scrape_anthropic_news(n=3)
    for item in items:
        print(f"\n--- {item['title']} ---")
        print(f"URL:  {item['url']}")
        print(f"Date: {item['date']}")
        print(f"Text: {item['raw_text'][:200]}...")
    print(f"\n{json.dumps(items, indent=2, ensure_ascii=False)}")
