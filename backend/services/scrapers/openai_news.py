"""OpenAI news scraper (RSS-first).

Returns list[dict] where each item has only:
- url
- title
- raw_text
- date
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

OPENAI_RSS_CANDIDATES = [
    "https://openai.com/news/rss.xml",
    "https://openai.com/rss.xml",
]
REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT}


def _clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _parse_rss_entries(xml_text: str, limit: int) -> list[dict[str, str]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    entries: list[dict[str, str]] = []
    for item in root.findall(".//item"):
        link = (item.findtext("link") or "").strip()
        title = _clean_whitespace((item.findtext("title") or "").strip())
        pub_date = (item.findtext("pubDate") or "").strip()
        description = _clean_whitespace((item.findtext("description") or "").strip())
        if not link:
            continue
        entries.append({"url": link, "title": title, "date": pub_date, "description": description})
        if len(entries) >= limit:
            break
    return entries


def _get_entries_from_rss(limit: int) -> list[dict[str, str]]:
    for feed_url in OPENAI_RSS_CANDIDATES:
        try:
            response = requests.get(feed_url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.RequestException:
            continue

        entries = _parse_rss_entries(response.text, limit)
        if entries:
            return entries
    return []


def _extract_date_from_page(soup: BeautifulSoup) -> str:
    time_tag = soup.select_one("time[datetime]")
    if time_tag and time_tag.get("datetime"):
        return time_tag["datetime"].strip()

    meta_pub = soup.select_one("meta[property='article:published_time']")
    if meta_pub and meta_pub.get("content"):
        return meta_pub["content"].strip()
    return ""


def _extract_full_body_text(soup: BeautifulSoup) -> str:
    for selector in ["article", "[data-page-content]", "main"]:
        container = soup.select_one(selector)
        if not container:
            continue

        paragraphs = [_clean_whitespace(p.get_text(" ", strip=True)) for p in container.select("p")]
        paragraphs = [p for p in paragraphs if p]
        if paragraphs:
            return _clean_whitespace(" ".join(paragraphs))

        text = _clean_whitespace(container.get_text(" ", strip=True))
        if text:
            return text

    return ""


def _fetch_article(url: str) -> dict[str, str]:
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("OpenAI article fetch failed for %s: %s", url, exc)
        return {"title": "", "raw_text": "", "date": ""}

    soup = BeautifulSoup(response.text, "html.parser")
    h1 = soup.select_one("h1")
    title = _clean_whitespace(h1.get_text(" ", strip=True)) if h1 else ""
    raw_text = _extract_full_body_text(soup)
    date = _extract_date_from_page(soup)
    return {"title": title, "raw_text": raw_text, "date": date}


def scrape_openai_news(n: int = 5) -> list[dict[str, Any]]:
    entries = _get_entries_from_rss(n)
    if not entries:
        logger.error("Could not read OpenAI RSS feed entries")
        return []

    results: list[dict[str, Any]] = []
    for entry in entries:
        detail = _fetch_article(entry["url"])
        results.append(
            {
                "url": entry["url"],
                "title": detail["title"] or entry["title"],
                "raw_text": detail["raw_text"] or entry.get("description", ""),
                "date": detail["date"] or entry["date"],
            }
        )
    return results
