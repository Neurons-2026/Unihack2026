from typing import Any, Dict, List

from duckduckgo_search import DDGS

from services.preprocessing import clean_card_summary, score_content_item

# Items scoring below this threshold trigger a supplementary search
LOW_QUALITY_THRESHOLD = 0.40

# Number of search result snippets to pull in
MAX_RESULTS = 3


def _build_query(item: Dict[str, Any]) -> str:
    """Build a focused search query from the item title and source."""
    title = item.get("title", "")
    source = item.get("source", "")

    # Strip source-specific noise for cleaner queries
    source_label = {
        "github": "GitHub",
        "huggingface": "Hugging Face",
        "arxiv_cs_ai": "research paper",
        "arxiv_cs_lg": "research paper",
        "arxiv_cs_cl": "research paper",
        "openai_blog": "OpenAI",
        "anthropic_blog": "Anthropic",
        "deepmind_blog": "DeepMind",
    }.get(source, "")

    query = f"{title} {source_label} AI".strip()
    return query


def _fetch_snippets(query: str, max_results: int = MAX_RESULTS) -> List[str]:
    """Run a DuckDuckGo text search and return clean snippets."""
    snippets: List[str] = []
    try:
        with DDGS() as ddgs:
            for result in ddgs.text(query, max_results=max_results):
                body = result.get("body", "").strip()
                if body:
                    snippets.append(clean_card_summary(body))
    except Exception:
        # Search failure is non-fatal — return whatever we got
        pass
    return snippets


def enrich_if_needed(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check the item's quality score (SU10 output). If it falls below
    LOW_QUALITY_THRESHOLD, run a DuckDuckGo search to pull in supplementary
    context snippets, append them to cleaned_text, and re-score.

    Requires item['preprocessing'] to be populated (SU3 + SU10 output).
    Sets item['preprocessing']['enrichment_used'] = True when search runs.
    Returns the updated item.
    """
    preprocessing = item.get("preprocessing", {})
    score = preprocessing.get("quality_score", 0.0)

    if score >= LOW_QUALITY_THRESHOLD:
        return item  # good enough — no enrichment needed

    query = _build_query(item)
    snippets = _fetch_snippets(query)

    if not snippets:
        return item  # search returned nothing — leave item as-is

    # Append snippets to cleaned_text as supplementary context
    existing_text = preprocessing.get("cleaned_text", "")
    supplementary = "\n\n".join(snippets)
    enriched_text = f"{existing_text}\n\n[Supplementary context]\n{supplementary}".strip()

    item["preprocessing"]["cleaned_text"] = enriched_text
    item["preprocessing"]["enrichment_used"] = True

    # Re-score with the richer text
    new_score, new_notes = score_content_item(item)
    item["preprocessing"]["quality_score"] = new_score
    item["preprocessing"]["quality_notes"] = new_notes

    return item
