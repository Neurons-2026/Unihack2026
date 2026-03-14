# Preprocessing Pipeline Summary

**Owner:** Sunny | **Files:** `backend/services/preprocessing.py`, `backend/services/enrichment.py`

---

## Pipeline Order

```
raw content_item (Sam's ingestion)
  → SU3: preprocess_content_item()
  → SU10: score_content_item()        ← called inside SU3
  → SU11: enrich_if_needed()
  → enriched content_item (ready for card generation)
```

---

## SU3 — HTML Stripping & Text Cleaning (`preprocess_content_item`)

Entry point for all raw content. Detects whether `raw_content` is HTML or plain text:

- **HTML path:** `readability-lxml` extracts the main article body (strips nav, ads, footers, sidebars), then BeautifulSoup removes remaining tags and any leftover `script`/`style`/`iframe` blocks
- **Plain text path:** light clean via BeautifulSoup + regex (for arXiv abstracts etc.)
- Both paths: Unicode normalisation (NFKC), whitespace collapse

Output written to `item["preprocessing"]["cleaned_text"]`.

---

## SU10 — Quality Scoring (`score_content_item`)

Scores each item 0–1 across three weighted dimensions:

| Dimension | Weight | Logic |
|---|---|---|
| Content length | 0–0.50 | `min(word_count / 400, 1.0) × 0.5` |
| Source authority | 0–0.30 | blogs = 0.30, arXiv/HuggingFace = 0.20, GitHub/other = 0.10 |
| Completeness | 0–0.20 | +0.05 each for title, raw_summary, published_at, metadata |

Also produces `quality_notes` (e.g. `short_content`, `rich_content`, `source_authoritative`, `has_summary`, `has_publish_date`).

Output written to `item["preprocessing"]["quality_score"]` and `item["preprocessing"]["quality_notes"]`.

---

## SU11 — Supplementary Search Enrichment (`enrich_if_needed`)

Triggered automatically when `quality_score < 0.40`. Uses DuckDuckGo (no API key required):

1. Builds a search query from `title` + mapped source label (e.g. `"BitNet GitHub AI"`)
2. Fetches top 3 result snippets, light-cleans each one
3. Appends to `cleaned_text` under a `[Supplementary context]` marker
4. Re-runs `score_content_item()` to update score with the richer text
5. Sets `enrichment_used: True`

Search failure is non-fatal — item passes through unchanged if DDG is unavailable.

---

## Full Output Shape

```json
{
  "preprocessing": {
    "cleaned_text": "main article text...\n\n[Supplementary context]\nweb snippet...",
    "quality_score": 0.72,
    "quality_notes": ["rich_content", "source_authoritative", "has_summary"],
    "enrichment_used": false
  }
}
```

---

## Integration Points

- **Upstream (Sam):** call `preprocess_content_item(item)` then `enrich_if_needed(item)` after ingestion
- **Downstream (card generation, SU4):** consume `item["preprocessing"]["cleaned_text"]`
- **Downstream (briefing, SU5):** same `cleaned_text` field
- **Downstream (ranking, Liam):** consume `quality_score` for feed ranking signals
