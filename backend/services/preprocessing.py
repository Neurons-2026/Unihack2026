"""Preprocessing helpers for news scrapers.

This module does not extract keywords. It consumes keywords provided by Harry's tool.
"""

from __future__ import annotations

import re
import unicodedata
from typing import List

from bs4 import BeautifulSoup
from readability import Document

from models.schemas import Card

MAX_TITLE_LEN = 80
MAX_SUMMARY_LEN = 120
MAX_PREVIEW_LEN = 320


def _clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    shortened = text[: max_len - 3].rsplit(" ", 1)[0]
    return shortened.rstrip(".,;:") + "..."


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def clean_article_text(raw_text: str) -> str:
    """Remove noisy metadata/citation lines while keeping full article content."""
    text = raw_text or ""
    lines = [line.strip() for line in text.splitlines()]
    cleaned_lines: list[str] = []

    date_prefix = re.compile(
        r"^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2},?\s+\d{4}\b",
        re.IGNORECASE,
    )
    retrieved_prefix = re.compile(r"^(retrieved|source:|references?:)\b", re.IGNORECASE)
    citation_block = re.compile(r"^\[\d+\]\s+")

    for line in lines:
        if not line:
            continue
        if date_prefix.match(line):
            continue
        if retrieved_prefix.match(line):
            continue
        if citation_block.match(line):
            continue
        cleaned_lines.append(line)

    return _clean_whitespace(" ".join(cleaned_lines))


def build_preview_text(cleaned_text: str, max_len: int = MAX_PREVIEW_LEN) -> str:
    """Create short preview text for cards while keeping cleaned_text full-length."""
    sentences = _split_sentences(cleaned_text)
    if not sentences:
        return _truncate(cleaned_text, max_len)

    preview = ""
    for sent in sentences:
        candidate = (preview + " " + sent).strip() if preview else sent
        if len(candidate) > max_len:
            break
        preview = candidate

    if not preview:
        preview = _truncate(cleaned_text, max_len)
    return preview


def build_text_views(raw_text: str) -> tuple[str, str]:
    """Return (cleaned_text, preview_text) from full raw text."""
    cleaned_text = clean_article_text(raw_text)
    preview_text = build_preview_text(cleaned_text)
    return cleaned_text, preview_text


def summarize_from_raw_text(raw_text: str, keywords: list[str]) -> tuple[str, str]:
    """Return (card_title, card_summary) from raw_text and provided keywords.

    Heuristic strategy:
    - card_title: first clean sentence fragment, optional keyword hint.
    - card_summary: best sentence that mentions a provided keyword, else first sentence.
    """
    text = _clean_whitespace(raw_text or "")
    sentences = _split_sentences(text)

    if sentences:
        first = sentences[0]
    elif keywords:
        first = f"Update on {', '.join(keywords[:2])}."
    else:
        first = "AI update."

    kw_lower = [k.lower() for k in keywords if k]
    best = ""
    for sent in sentences[:12]:
        low = sent.lower()
        if any(k in low for k in kw_lower):
            best = sent
            break
    if not best:
        best = first

    base_title = first.rstrip(".!? ")
    if not base_title and keywords:
        base_title = f"Update: {', '.join(keywords[:2])}"
    elif not base_title:
        base_title = "AI News Update"

    card_title = _truncate(base_title, MAX_TITLE_LEN)
    card_summary = _truncate(best, MAX_SUMMARY_LEN)
    return card_title, card_summary


def scraped_item_to_card(item: dict, keywords: list[str], source: str) -> dict:
    """Convert scraper output + provided keywords into a card-shaped dict."""
    raw_text = item.get("raw_text", "")
    cleaned_text, preview_text = build_text_views(raw_text)
    summary_input = preview_text or cleaned_text or raw_text
    card_title, card_summary = summarize_from_raw_text(summary_input, keywords)
    url = item.get("url", "")
    slug = url.rstrip("/").split("/")[-1] if url else "unknown"

    return {
        "id": f"{source}:{slug}",
        "card_title": card_title,
        "card_summary": card_summary,
        "keywords": keywords,
        "source": source,
        "source_url": url,
        "thumbnail_keyword": keywords[0] if keywords else source,
    }


def extract_plaintext(html: str) -> str:
    """Strip boilerplate/ads from raw HTML and return clean plaintext."""
    # readability-lxml pulls the main article content, discarding nav/ads/footers
    doc = Document(html)
    cleaned_html = doc.summary(html_partial=True)

    # BeautifulSoup strips remaining tags
    soup = BeautifulSoup(cleaned_html, "html.parser")

    # Remove any leftover script/style blocks readability missed
    for tag in soup(["script", "style", "noscript", "iframe", "form"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Normalise unicode (e.g. curly quotes, soft hyphens)
    text = unicodedata.normalize("NFKC", text)

    # Collapse excessive whitespace / blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    return text


def clean_card_summary(summary: str) -> str:
    """Light clean for summaries that arrive as plain text (not full HTML)."""
    # Strip any stray HTML tags
    soup = BeautifulSoup(summary, "html.parser")
    text = soup.get_text(separator=" ")
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def preprocess_cards(raw_cards: List[Card]) -> List[Card]:
    """
    Clean card summaries.
    When Sam's ingestion pipeline passes full HTML bodies in the future,
    call extract_plaintext() on the raw HTML before building the Card.
    For now, sanitise whatever summary text arrives.
    """
    cleaned = []
    for card in raw_cards:
        cleaned_summary = clean_card_summary(card.card_summary)
        cleaned.append(card.copy(update={"card_summary": cleaned_summary}))
    return cleaned
