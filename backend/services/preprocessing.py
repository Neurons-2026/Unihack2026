"""
Preprocessing and summarization for the scraper-to-card pipeline.

Pipeline flow:
  1. Scrapers produce: {url, title, raw_text, date}
  2. Harry's keyword extractor produces: keywords[]
  3. This module takes (raw_text, keywords) and generates:
     - card_title: clean, concise title
     - card_summary: 1-line summary < 120 chars
"""

from __future__ import annotations

import re
from typing import List

from models.schemas import Card


def _clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len, breaking at word boundary."""
    if len(text) <= max_len:
        return text
    truncated = text[: max_len - 3].rsplit(" ", 1)[0]
    return truncated.rstrip(".,;:") + "..."


def generate_card_summary(raw_text: str, keywords: list[str]) -> str:
    """
    Generate a concise 1-line card_summary (< 120 chars) from raw_text and keywords.

    Strategy:
    1. Find the first sentence in raw_text that contains any keyword.
    2. If none found, use the first sentence.
    3. Truncate to < 120 chars.
    """
    if not raw_text:
        # Fallback: build from keywords
        if keywords:
            return _truncate(f"Latest on {', '.join(keywords[:3])}.", 120)
        return "New AI development."

    text = _clean_whitespace(raw_text)
    sentences = re.split(r"(?<=[.!?])\s+", text)

    # Try to find a sentence mentioning a keyword
    kw_lower = {kw.lower() for kw in keywords}
    for sentence in sentences[:10]:  # only check first 10 sentences
        sentence_lower = sentence.lower()
        if any(kw in sentence_lower for kw in kw_lower):
            return _truncate(_clean_whitespace(sentence), 120)

    # Fallback: first sentence
    if sentences:
        return _truncate(_clean_whitespace(sentences[0]), 120)

    return _truncate(text, 120)


def generate_card_title(raw_title: str, keywords: list[str]) -> str:
    """
    Clean up a raw title for card display.

    Removes source prefixes, trims whitespace, and ensures reasonable length.
    """
    if not raw_title:
        if keywords:
            return _truncate(f"Update: {', '.join(keywords[:3])}", 80)
        return "AI News Update"

    title = _clean_whitespace(raw_title)

    # Remove common prefixes that scrapers pick up
    for prefix in ["Announcements ", "Product ", "Research ", "Policy "]:
        if title.startswith(prefix):
            title = title[len(prefix):]

    return _truncate(title, 80)


def scraped_item_to_card(
    item: dict,
    keywords: list[str],
    card_id: str | None = None,
    source: str = "unknown",
) -> dict:
    """
    Convert a scraped item + keywords into a card dict ready for the Card schema.

    Args:
        item: dict with {url, title, raw_text, date} from a scraper
        keywords: list of keywords from Harry's extractor
        card_id: optional custom ID; defaults to source:slug
        source: source name (e.g. "openai", "anthropic")

    Returns:
        dict matching the Card schema fields.
    """
    url = item.get("url", "")
    raw_title = item.get("title", "")
    raw_text = item.get("raw_text", "")

    # Generate ID from URL slug if not provided
    if not card_id:
        slug = url.rstrip("/").split("/")[-1] if url else "unknown"
        card_id = f"{source}:{slug}"

    card_title = generate_card_title(raw_title, keywords)
    card_summary = generate_card_summary(raw_text, keywords)

    return {
        "id": card_id,
        "card_title": card_title,
        "card_summary": card_summary,
        "keywords": keywords,
        "source": source,
        "source_url": url,
        "thumbnail_keyword": keywords[0] if keywords else source,
    }


async def preprocess_cards(raw_cards: List[Card]) -> List[Card]:
    """Backwards-compatible pass-through for existing Card objects."""
    return raw_cards


if __name__ == "__main__":
    # Quick test
    test_item = {
        "url": "https://www.anthropic.com/news/claude-sonnet-4-6",
        "title": "Introducing Claude Sonnet 4.6",
        "raw_text": (
            "Claude Sonnet 4.6 is our most capable Sonnet model yet. "
            "It's a full upgrade of the model's skills across coding, computer use, "
            "long-context reasoning, agent planning, knowledge work, and design. "
            "Sonnet 4.6 also features a 1M token context window."
        ),
        "date": "Feb 17, 2026",
    }
    test_keywords = ["claude", "sonnet", "coding", "reasoning"]

    card = scraped_item_to_card(test_item, test_keywords, source="anthropic")

    print(f"ID:      {card['id']}")
    print(f"Title:   {card['card_title']}")
    print(f"Summary: {card['card_summary']}")
    print(f"Keywords: {card['keywords']}")
    print(f"Len(summary): {len(card['card_summary'])}")
