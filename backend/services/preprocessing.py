"""Preprocessing helpers for the 10min-AI-Daily pipeline.

This module does not extract keywords. It consumes keywords provided by Harry's tool.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from models.schemas import Card

MAX_TITLE_LEN = 80
MAX_SUMMARY_LEN = 120
MAX_PREVIEW_LEN = 320

# Source authority tiers (used by quality scoring)
_HIGH_AUTHORITY = {"anthropic_blog", "openai_blog", "deepmind_blog"}
_MID_AUTHORITY = {"arxiv_cs_ai", "arxiv_cs_lg", "arxiv_cs_cl", "huggingface"}


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


# =========================================================================
# Source-specific cleaners (Sunny — preprocessing owner)
# =========================================================================

_GITHUB_NOISE = re.compile(
    r"(?i)^(#{1,3}\s*)?(installation|install|getting started|prerequisites|"
    r"requirements|contributing|license|faq|troubleshooting|usage:)\b"
)
_GITHUB_BADGE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_GITHUB_CMD = re.compile(
    r"^\s*(pip install|npm install|conda |git clone|docker |brew |cargo |go get)\b"
)


def _clean_github(text: str) -> str:
    """Remove install commands, badges, boilerplate README sections."""
    lines = text.splitlines()
    cleaned: list[str] = []
    skip_section = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _GITHUB_NOISE.match(stripped):
            skip_section = True
            continue
        if re.match(r"^#{1,3}\s+", stripped) and not _GITHUB_NOISE.match(stripped):
            skip_section = False
        if skip_section:
            continue
        stripped = _GITHUB_BADGE.sub("", stripped).strip()
        if not stripped:
            continue
        if _GITHUB_CMD.match(stripped):
            continue
        cleaned.append(stripped)

    return _clean_whitespace(" ".join(cleaned))


def _clean_huggingface(text: str) -> str:
    """Remove duplicate abstract snippets and footer noise from HF/arXiv."""
    lines = text.splitlines()
    seen: set[str] = set()
    cleaned: list[str] = []

    footer = re.compile(
        r"(?i)^(downloaded from|cite as|bibtex|@article|@inproceedings|"
        r"published in|proceedings of|arxiv:\d)"
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if footer.match(stripped):
            continue
        key = stripped.lower()[:120]
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(stripped)

    return _clean_whitespace(" ".join(cleaned))


_BLOG_META = re.compile(
    r"(?i)^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2},?\s+\d{4}\b"
)
_BLOG_NOISE = re.compile(
    r"(?i)^(retrieved|source:|references?:|share this|follow us|subscribe)\b"
)
_CITATION_BLOCK = re.compile(r"^\[\d+\]\s+")


def _clean_blog(text: str) -> str:
    """Strip metadata patterns from OpenAI/Anthropic blog content."""
    lines = text.splitlines()
    cleaned: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _BLOG_META.match(stripped):
            continue
        if _BLOG_NOISE.match(stripped):
            continue
        if _CITATION_BLOCK.match(stripped):
            continue
        cleaned.append(stripped)

    return _clean_whitespace(" ".join(cleaned))


def clean_by_source(raw_text: str, source: str) -> str:
    """Dispatch to the right source-specific cleaner."""
    if source == "github":
        return _clean_github(raw_text)
    if source in ("huggingface", "arxiv_cs_ai", "arxiv_cs_lg", "arxiv_cs_cl"):
        return _clean_huggingface(raw_text)
    if source in ("openai_blog", "anthropic_blog", "deepmind_blog"):
        return _clean_blog(raw_text)
    return _clean_whitespace(raw_text or "")


# =========================================================================
# Quality scoring
# =========================================================================

def score_content_item(item: Dict[str, Any]) -> tuple[float, list[str]]:
    """
    Score a preprocessed content_item 0-1.

    Breakdown (max 1.0):
      Content length  0-0.50  (word count, saturates at 400)
      Source authority 0-0.30  (tier-based)
      Completeness    0-0.20  (presence of key fields)
    """
    notes: list[str] = []
    cleaned_text = item.get("preprocessing", {}).get("cleaned_text", "")
    word_count = len(cleaned_text.split())

    length_score = min(word_count / 400, 1.0) * 0.50
    if word_count < 80:
        notes.append("short_content")
    elif word_count >= 300:
        notes.append("rich_content")

    source = item.get("source", "")
    if source in _HIGH_AUTHORITY:
        authority_score = 0.30
        notes.append("source_authoritative")
    elif source in _MID_AUTHORITY:
        authority_score = 0.20
    else:
        authority_score = 0.10

    completeness_score = 0.0
    if item.get("title", "").strip():
        completeness_score += 0.05
    if item.get("raw_summary", "").strip():
        completeness_score += 0.05
        notes.append("has_summary")
    if item.get("published_at", ""):
        completeness_score += 0.05
        notes.append("has_publish_date")
    if item.get("metadata"):
        completeness_score += 0.05

    score = round(length_score + authority_score + completeness_score, 3)
    return score, notes


# =========================================================================
# Full preprocessing for a single content_item (used by runner)
# =========================================================================

def preprocess_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean raw_content by source, build preview, score quality.

    Does NOT call LLM — that happens in the runner via card_generation.py.
    Does NOT overwrite raw_content.
    """
    source = item.get("source", "other")
    raw_content = item.get("raw_content", "")

    cleaned_text = clean_by_source(raw_content, source)
    preview_text = build_preview_text(cleaned_text)

    existing_notes = item.get("preprocessing", {}).get("quality_notes", [])

    item["preprocessing"] = {
        "cleaned_text": cleaned_text,
        "preview_text": preview_text,
        "quality_score": 0.0,
        "quality_notes": list(existing_notes),
        "enrichment_used": item.get("preprocessing", {}).get("enrichment_used", False),
    }

    score, notes = score_content_item(item)
    item["preprocessing"]["quality_score"] = score
    item["preprocessing"]["quality_notes"].extend(notes)

    item["pipeline_state"] = "preprocessed"
    return item


# =========================================================================
# Legacy / backwards-compatible functions
# =========================================================================

async def preprocess_cards(raw_cards: List[Card]) -> List[Card]:
    # Backwards-compatible pass-through for existing Card objects.
    return raw_cards
