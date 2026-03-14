import json
import re
from typing import Any, Dict, List

import anthropic

from config import get_settings

SYSTEM_PROMPT = """You generate structured metadata for AI news cards. You will receive the title, source, and cleaned article text for one news item. Return a JSON object with exactly these four fields:

{
  "card_title": "A concise, jargon-free headline (max 80 characters, present tense, active voice)",
  "card_summary": "One sentence explaining the news for a non-technical reader (max 120 characters, no jargon)",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "thumbnail_keyword": "single concrete noun for image search (e.g. robot, chip, graph)"
}

Rules:
- card_title: max 80 chars, no clickbait, plain English, present tense
- card_summary: max 120 chars — if a technical term is unavoidable, explain it in plain English inline
- keywords: 3 to 5 items, lowercase, single words or short hyphenated phrases, most specific first
- thumbnail_keyword: one word, concrete and visual
- Output valid JSON only — no prose, no markdown fences, no explanation"""


def _build_user_prompt(item: Dict[str, Any]) -> str:
    title = item.get("title", "")
    source = item.get("source", "")
    cleaned_text = item.get("preprocessing", {}).get("cleaned_text", "") or item.get("raw_summary", "")
    # Truncate to ~1500 words to stay within token budget
    words = cleaned_text.split()
    if len(words) > 1500:
        cleaned_text = " ".join(words[:1500]) + " [truncated]"
    return f"Title: {title}\nSource: {source}\n\nContent:\n{cleaned_text}"


def _parse_card_fields(raw: str) -> Dict[str, Any]:
    """Extract the JSON object from Claude's response."""
    # Strip markdown fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    data = json.loads(raw)

    card_title = str(data.get("card_title", "")).strip()[:80]
    card_summary = str(data.get("card_summary", "")).strip()[:120]

    keywords: List[str] = [str(k).lower().strip() for k in data.get("keywords", [])]
    keywords = keywords[:5]  # cap at 5

    thumbnail_keyword = str(data.get("thumbnail_keyword", "")).strip().split()[0] if data.get("thumbnail_keyword") else ""

    return {
        "card_title": card_title,
        "card_summary": card_summary,
        "keywords": keywords,
        "thumbnail_keyword": thumbnail_keyword,
    }


def generate_card_fields(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call Claude to produce card_title, card_summary, keywords, and thumbnail_keyword
    for a preprocessed content_item dict (S2 schema).

    Populates item['card'] and returns the updated dict.
    Requires item['preprocessing']['cleaned_text'] to be set (SU3 output).
    """
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    user_prompt = _build_user_prompt(item)

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": user_prompt}],
        system=SYSTEM_PROMPT,
    )

    raw_response = message.content[0].text
    card_fields = _parse_card_fields(raw_response)

    item["card"] = card_fields
    return item


def generate_card_fields_batch(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process a list of content_items sequentially. Returns all items with card fields populated."""
    return [generate_card_fields(item) for item in items]
