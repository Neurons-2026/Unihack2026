import json
import re
from typing import Any, Dict, List

import anthropic

from config import get_settings

SYSTEM_PROMPT = """You generate structured metadata for AI news cards. You will receive the title, source, cleaned article text, and a list of extracted technical concepts for one news item. Return a JSON object with exactly these four fields:

{
  "card_title": "A concise, jargon-free headline (max 80 characters, present tense, active voice)",
  "card_summary": "One sentence explaining the news for a non-technical reader (max 120 characters, no jargon)",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "thumbnail_keyword": "single concrete noun for image search (e.g. robot, chip, graph)"
}

Rules:
- card_title: MUST be under 80 characters. No clickbait, plain English, present tense
- card_summary: MUST be a COMPLETE sentence that ends naturally with a period. HARD LIMIT: 110 characters. Count your characters carefully before responding. If over 110 characters, rewrite shorter. No jargon — if a technical term is unavoidable, explain it in plain English inline
- keywords: 3 to 5 items, lowercase, single words or short hyphenated phrases, most specific first. IMPORTANT: The keywords list MUST include the extracted concept labels provided below. Place concept labels first, then add 1-2 additional contextual keywords if needed to reach 3-5 total. Do NOT drop or rephrase the concept labels — use them exactly as given.
- thumbnail_keyword: one word, concrete and visual
- Output valid JSON only — no prose, no markdown fences, no explanation"""


def _build_user_prompt(item: Dict[str, Any], concept_labels: List[str] | None = None) -> str:
    title = item.get("title", "")
    source = item.get("source", "")
    cleaned_text = item.get("preprocessing", {}).get("cleaned_text", "") or item.get("raw_summary", "")
    # Truncate to ~1500 words to stay within token budget
    words = cleaned_text.split()
    if len(words) > 1500:
        cleaned_text = " ".join(words[:1500]) + " [truncated]"

    prompt = f"Title: {title}\nSource: {source}\n\nContent:\n{cleaned_text}"

    if concept_labels:
        labels_str = ", ".join(concept_labels)
        prompt += (
            f"\n\nExtracted Concepts (MUST appear as keywords):\n{labels_str}"
        )

    return prompt


def _truncate_clean(text: str, max_len: int) -> str:
    """Truncate to max_len at a word boundary, ending with a period."""
    if len(text) <= max_len:
        return text
    shortened = text[: max_len - 1].rsplit(" ", 1)[0].rstrip(".,;:!? ")
    return shortened + "."


def _parse_card_fields(raw: str, concept_labels: List[str] | None = None) -> Dict[str, Any]:
    """Extract the JSON object from Claude's response."""
    # Strip markdown fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    data = json.loads(raw)

    card_title = _truncate_clean(str(data.get("card_title", "")).strip(), 80)
    card_summary = _truncate_clean(str(data.get("card_summary", "")).strip(), 120)

    keywords: List[str] = [str(k).lower().strip() for k in data.get("keywords", [])]

    # Ensure concept labels are always present in keywords
    if concept_labels:
        existing_set = set(keywords)
        # Prepend any missing concept labels
        missing = [label.lower().strip() for label in concept_labels if label.lower().strip() not in existing_set]
        keywords = missing + keywords

    keywords = keywords[:5]  # cap at 5

    thumbnail_keyword = str(data.get("thumbnail_keyword", "")).strip().split()[0] if data.get("thumbnail_keyword") else ""

    return {
        "card_title": card_title,
        "card_summary": card_summary,
        "keywords": keywords,
        "thumbnail_keyword": thumbnail_keyword,
    }


def generate_card_fields(
    item: Dict[str, Any],
    concept_labels: List[str] | None = None,
) -> Dict[str, Any]:
    """
    Call Claude to produce card_title, card_summary, keywords, and thumbnail_keyword
    for a preprocessed content_item dict (S2 schema).

    Args:
        item: Content item dict with preprocessing.cleaned_text set.
        concept_labels: List of extracted concept labels to include as keywords.

    Populates item['card'] and returns the updated dict.
    """
    import os
    settings = get_settings()
    api_key = (
        settings.anthropic_api_key
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ANTHTROPIC_API")
    )
    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = _build_user_prompt(item, concept_labels)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": user_prompt}],
        system=SYSTEM_PROMPT,
    )

    raw_response = message.content[0].text
    card_fields = _parse_card_fields(raw_response, concept_labels)

    # If Harry's keywords exist in metadata, merge with concept labels
    harry_keywords = item.get("metadata", {}).get("keywords", [])
    if harry_keywords and not concept_labels:
        card_fields["keywords"] = [str(k).lower().strip() for k in harry_keywords[:5]]

    # Auto-fetch a relevant image from Pexels
    try:
        from services.image_search import get_card_image
        image_url = get_card_image(
            keywords=card_fields.get("keywords", []),
            title=item.get("title", ""),
            thumbnail_keyword=card_fields.get("thumbnail_keyword", ""),
        )
        if image_url:
            card_fields["image_url"] = image_url
    except Exception:
        pass  # Non-critical

    item["card"] = card_fields
    return item


def generate_card_fields_batch(
    items: List[Dict[str, Any]],
    concepts_by_item: Dict[str, List[str]] | None = None,
) -> List[Dict[str, Any]]:
    """Process a list of content_items sequentially.

    Args:
        items: List of content item dicts.
        concepts_by_item: Optional mapping of item_id -> list of concept labels.

    Returns all items with card fields populated.
    """
    result = []
    for item in items:
        labels = (concepts_by_item or {}).get(item.get("id", ""))
        result.append(generate_card_fields(item, concept_labels=labels))
    return result
