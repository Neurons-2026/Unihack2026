"""Anthropic news scraper.

Returns list[dict] where each item has only:
- url
- title
- raw_text
- date
"""

from __future__ import annotations

import logging
import re
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

ANTHROPIC_NEWS_URL = "https://www.anthropic.com/news"
REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT}


def _clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_article_urls(listing_html: str, limit: int) -> list[str]:
    soup = BeautifulSoup(listing_html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()

    for link in soup.select("a[href]"):
        href = (link.get("href") or "").strip()
        if href.startswith("/news/") and href != "/news/":
            url = f"https://www.anthropic.com{href}"
        elif href.startswith("https://www.anthropic.com/news/") and href.rstrip("/") != ANTHROPIC_NEWS_URL:
            url = href
        else:
            continue

        canonical = url.rstrip("/")
        if canonical in seen:
            continue
        seen.add(canonical)
        urls.append(url)
        if len(urls) >= limit:
            break

    return urls


def _extract_date_from_page(soup: BeautifulSoup) -> str:
    meta_pub = soup.select_one("meta[property='article:published_time']")
    if meta_pub and meta_pub.get("content"):
        return meta_pub["content"].strip()

    time_tag = soup.select_one("time[datetime]")
    if time_tag and time_tag.get("datetime"):
        return time_tag["datetime"].strip()

    text = _clean_whitespace((soup.select_one("article") or soup.select_one("main") or soup).get_text(" ", strip=True))
    m = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}", text)
    return m.group(0) if m else ""


def _extract_full_body_text(soup: BeautifulSoup) -> str:
    container = soup.select_one("article") or soup.select_one("main")
    if not container:
        return ""

    # Build full text from all paragraphs, no intentional truncation.
    paragraphs = [_clean_whitespace(p.get_text(" ", strip=True)) for p in container.select("p")]
    paragraphs = [p for p in paragraphs if p]
    if paragraphs:
        return _clean_whitespace(" ".join(paragraphs))

    return _clean_whitespace(container.get_text(" ", strip=True))


def _fetch_article(url: str) -> dict[str, str]:
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Anthropic article fetch failed for %s: %s", url, exc)
        return {"title": "", "raw_text": "", "date": ""}

    soup = BeautifulSoup(response.text, "html.parser")
    h1 = soup.select_one("h1")
    title = _clean_whitespace(h1.get_text(" ", strip=True)) if h1 else ""
    raw_text = _extract_full_body_text(soup)
    date = _extract_date_from_page(soup)
    return {"title": title, "raw_text": raw_text, "date": date}


def scrape_anthropic_news(n: int = 5) -> list[dict[str, Any]]:
    try:
        response = requests.get(ANTHROPIC_NEWS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to fetch Anthropic news listing: %s", exc)
        return []

    article_urls = _extract_article_urls(response.text, n)
    if not article_urls:
        return []

    results: list[dict[str, Any]] = []
    for url in article_urls:
        detail = _fetch_article(url)
        if not detail["title"]:
            # Enforce title source from article-page <h1> only.
            continue
        results.append(
            {
                "url": url,
                "title": detail["title"],
                "raw_text": detail["raw_text"],
                "date": detail["date"],
            }
        )

    return results
