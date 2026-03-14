"""Preprocessing runner — reads content_items, cleans, calls LLM, writes card-ready output.

Usage:
    cd backend
    python -m scripts.run_preprocessing
    python -m scripts.run_preprocessing --source github_trending
    python -m scripts.run_preprocessing --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure backend/ is on sys.path so imports work when run as a script
_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from services.preprocessing import preprocess_item, summarize_from_raw_text
from services.card_generation import generate_card_fields

# Source folder names under backend/data/scraped/
SOURCES = [
    "github_trending",
    "huggingface_papers",
    "openai_news",
    "anthropic_news",
]

DATA_ROOT = _BACKEND / "data" / "scraped"


def _load_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _apply_llm_card_fields(item: dict) -> dict:
    """Call LLM for card fields; fall back to heuristic on failure."""
    try:
        item = generate_card_fields(item)
        item["preprocessing"]["quality_notes"].append("llm_summary_generated")
        return item
    except Exception as exc:
        print(f"  [WARN] LLM failed for {item.get('id', '?')}: {exc}")
        # Heuristic fallback
        cleaned = item.get("preprocessing", {}).get("cleaned_text", "")
        keywords = item.get("card", {}).get("keywords", []) or \
                   item.get("metadata", {}).get("keywords", [])
        title, summary = summarize_from_raw_text(cleaned, keywords)
        item["card"] = {
            "card_title": title,
            "card_summary": summary,
            "keywords": keywords[:5] if keywords else [],
            "thumbnail_keyword": keywords[0] if keywords else item.get("source", "ai"),
        }
        item["preprocessing"]["quality_notes"].append("llm_summary_fallback_used")
        return item


def _item_to_card_dict(item: dict) -> dict:
    """Extract flat card dict from a processed content_item."""
    card = item.get("card", {})
    return {
        "id": item.get("id", ""),
        "card_title": card.get("card_title", ""),
        "card_summary": card.get("card_summary", ""),
        "keywords": card.get("keywords", []),
        "source": item.get("source", ""),
        "source_url": item.get("source_url", ""),
        "thumbnail_keyword": card.get("thumbnail_keyword", ""),
    }


def process_source(source_dir: str, dry_run: bool = False) -> int:
    """Process all content_items for one source. Returns count of items processed."""
    latest_dir = DATA_ROOT / source_dir / "latest"
    items_path = latest_dir / "content_items_latest.json"

    items = _load_json(items_path)
    if not items:
        print(f"  No content_items found in {items_path}")
        return 0

    processed_items: list[dict] = []
    cards: list[dict] = []

    for item in items:
        print(f"  Processing: {item.get('id', '?')}")

        # Step 1: Source-specific cleaning + quality scoring
        item = preprocess_item(item)

        # Step 2: LLM card generation (with heuristic fallback)
        item = _apply_llm_card_fields(item)

        # Step 3: Mark card_ready
        item["pipeline_state"] = "card_ready"

        processed_items.append(item)
        cards.append(_item_to_card_dict(item))

    if dry_run:
        print(f"  [DRY RUN] Would write {len(processed_items)} items")
        for c in cards:
            print(f"    {c['card_title'][:60]} | {c['card_summary'][:60]}")
        return len(processed_items)

    # Write updated content_items and cards
    _save_json(items_path, processed_items)
    _save_json(latest_dir / "cards_latest.json", cards)

    # Also write timestamped snapshot
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_dir = DATA_ROOT / source_dir / date_str
    _save_json(date_dir / f"content_items_{ts}.json", processed_items)
    _save_json(date_dir / f"cards_{ts}.json", cards)

    print(f"  Wrote {len(processed_items)} items + cards")
    return len(processed_items)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run preprocessing pipeline")
    parser.add_argument(
        "--source",
        choices=SOURCES,
        help="Process a single source (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview output without writing files",
    )
    args = parser.parse_args()

    sources = [args.source] if args.source else SOURCES
    total = 0

    for src in sources:
        print(f"\n=== {src} ===")
        total += process_source(src, dry_run=args.dry_run)

    print(f"\nDone. Processed {total} items across {len(sources)} source(s).")


if __name__ == "__main__":
    main()
