"""Preprocessing helpers for news scrapers.

This module does not extract keywords. It consumes keywords provided by Harry's tool.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List

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


# Source authority tiers used by score_content_item()
_HIGH_AUTHORITY_SOURCES = {"anthropic_blog", "openai_blog", "deepmind_blog"}
_MID_AUTHORITY_SOURCES  = {"arxiv_cs_ai", "arxiv_cs_lg", "arxiv_cs_cl", "huggingface"}
_LOW_AUTHORITY_SOURCES  = {"github", "other"}


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


def score_content_item(item: Dict[str, Any]) -> tuple[float, list[str]]:
    """
    Score a preprocessed content_item 0–1 across three dimensions.

    Scoring breakdown (max 1.0):
      Content length   0–0.50  — based on cleaned_text word count
      Source authority 0–0.30  — based on source tier
      Completeness     0–0.20  — presence of key fields

    Returns (score, quality_notes).
    Requires item['preprocessing']['cleaned_text'] to be set (SU3 output).
    """
    notes: list[str] = []
    cleaned_text = item.get("preprocessing", {}).get("cleaned_text", "")
    word_count = len(cleaned_text.split())

    # --- Content length (0–0.50) ---
    # Saturates at 400 words; short items are penalised
    length_score = min(word_count / 400, 1.0) * 0.50
    if word_count < 80:
        notes.append("short_content")
    elif word_count >= 300:
        notes.append("rich_content")

    # --- Source authority (0–0.30) ---
    source = item.get("source", "")
    if source in _HIGH_AUTHORITY_SOURCES:
        authority_score = 0.30
        notes.append("source_authoritative")
    elif source in _MID_AUTHORITY_SOURCES:
        authority_score = 0.20
    else:
        authority_score = 0.10  # github / other

    # --- Completeness (0–0.20) ---
    completeness_score = 0.0
    if item.get("title", "").strip():
        completeness_score += 0.05
    if item.get("raw_summary", "").strip():
        completeness_score += 0.05
        notes.append("has_summary")
    if item.get("published_at", "").strip():
        completeness_score += 0.05
        notes.append("has_publish_date")
    if item.get("metadata"):
        completeness_score += 0.05

    score = round(length_score + authority_score + completeness_score, 3)
    return score, notes


def preprocess_content_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Take a content_item dict (S2 schema) with raw_content HTML,
    strip boilerplate, and populate item['preprocessing'].

    Returns the same dict with 'preprocessing' filled in.
    """
    raw_content = item.get("raw_content", "")

    if raw_content.strip().startswith("<"):
        cleaned_text = extract_plaintext(raw_content)
    else:
        # raw_content is already plain text (e.g. arXiv abstract)
        cleaned_text = clean_card_summary(raw_content)

    item["preprocessing"] = {
        "cleaned_text": cleaned_text,
        "quality_score": 0.0,   # placeholder; filled by score_content_item below
        "quality_notes": [],
        "enrichment_used": False,
    }

    score, notes = score_content_item(item)
    item["preprocessing"]["quality_score"] = score
    item["preprocessing"]["quality_notes"] = notes
    return item


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
