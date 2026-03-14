"""Preprocessing runner — reads content_items, cleans, calls LLM, writes to JSON + Supabase.

Usage:
    cd backend
    python -m scripts.run_preprocessing
    python -m scripts.run_preprocessing --source huggingface_papers
    python -m scripts.run_preprocessing --dry-run
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure backend/ is on sys.path so imports work when run as a script
_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from dotenv import load_dotenv
load_dotenv(_BACKEND / ".env")

from services.preprocessing import preprocess_item, summarize_from_raw_text
from services.card_generation import generate_card_fields
from models.database import get_supabase

# Source folder names under backend/data/scraped/
SOURCES = [
    "github_trending",
    "huggingface_papers",
    "openai_news",
    "anthropic_news",
]

DATA_ROOT = _BACKEND / "data" / "scraped"
CONCEPTS_DIR = _BACKEND / "data" / "concepts"


def _load_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _load_keyword_map() -> dict[str, list[str]]:
    """Load Harry's concept labels as keywords from backend/data/concepts/."""
    keyword_map: dict[str, list[str]] = {}
    for f in glob.glob(str(CONCEPTS_DIR / "*.json")):
        data = json.load(open(f, encoding="utf-8"))
        basename = os.path.basename(f).replace("_concepts.json", "")
        paper_id = "huggingface:" + basename
        keyword_map[paper_id] = [c["label"] for c in data.get("concepts", [])[:5]]
    return keyword_map


def _load_concepts(item_id: str) -> list[dict]:
    """Load full concept data for a content_item if available."""
    # Extract paper id (e.g. "huggingface:2603.12255" -> "2603.12255")
    paper_id = item_id.split(":", 1)[-1] if ":" in item_id else item_id
    concept_file = CONCEPTS_DIR / f"{paper_id}_concepts.json"
    if not concept_file.exists():
        return []
    data = json.load(open(concept_file, encoding="utf-8"))
    return data.get("concepts", [])


def _apply_llm_card_fields(item: dict) -> dict:
    """Call LLM for card fields; fall back to heuristic on failure."""
    try:
        item = generate_card_fields(item)
        item["preprocessing"]["quality_notes"].append("llm_summary_generated")
        return item
    except Exception as exc:
        print(f"  [WARN] LLM failed for {item.get('id', '?')}: {exc}")
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
        "thumbnail_keyword": card.get("thumbnail_keyword", ""),
    }


def _upsert_to_supabase(processed_items: list[dict], cards: list[dict]) -> None:
    """Write content_items and cards to Supabase.

    Actual DB schema (set up by team):
      content_items: id, schema_version, source, source_url, title, raw_summary,
                     raw_content, metadata, fetched_at, published_at, provenance, created_at
      cards: id, card_title, card_summary, keywords, thumbnail_keyword,
             cleaned_text, quality_score, trending_score, image_url, created_at
    """
    try:
        db = get_supabase()
    except Exception as exc:
        print(f"  [WARN] Supabase connection failed: {exc}")
        return

    # Upsert content_items (raw data — matches team's schema)
    for item in processed_items:
        row = {
            "id": item["id"],
            "schema_version": item.get("schema_version", "1.0.0"),
            "source": item["source"],
            "source_url": item["source_url"],
            "title": item["title"],
            "raw_summary": item.get("raw_summary", ""),
            "raw_content": item.get("raw_content", ""),
            "metadata": item.get("metadata", {}),
            "fetched_at": item.get("fetched_at"),
            "published_at": item.get("published_at"),
            "provenance": item.get("provenance", {}),
        }
        try:
            db.table("content_items").upsert(row).execute()
        except Exception as exc:
            print(f"  [WARN] content_items upsert failed for {item['id']}: {exc}")

    # Upsert cards (preprocessing outputs go here — cleaned_text, quality_score)
    for item, card in zip(processed_items, cards):
        pre = item.get("preprocessing", {})
        row = {
            "id": card["id"],
            "card_title": card["card_title"],
            "card_summary": card["card_summary"],
            "keywords": card["keywords"],
            "thumbnail_keyword": card.get("thumbnail_keyword", ""),
            "cleaned_text": pre.get("cleaned_text", ""),
            "quality_score": pre.get("quality_score", 0),
        }
        try:
            db.table("cards").upsert(row).execute()
        except Exception as exc:
            print(f"  [WARN] cards upsert failed for {card['id']}: {exc}")

    print(f"  Supabase: upserted {len(processed_items)} content_items + {len(cards)} cards")


def process_source(source_dir: str, dry_run: bool = False) -> int:
    """Process all content_items for one source. Returns count of items processed."""
    latest_dir = DATA_ROOT / source_dir / "latest"
    items_path = latest_dir / "content_items_latest.json"

    items = _load_json(items_path)
    if not items:
        print(f"  No content_items found in {items_path}")
        return 0

    # Load Harry's keywords
    keyword_map = _load_keyword_map()

    processed_items: list[dict] = []
    cards: list[dict] = []

    for item in items:
        print(f"  Processing: {item.get('id', '?')}")

        # Merge Harry's keywords if available
        item_id = item.get("id", "")
        if item_id in keyword_map:
            item["metadata"]["keywords"] = keyword_map[item_id]
            print(f"    Merged {len(keyword_map[item_id])} keywords from concepts")

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

    # Write to JSON files
    _save_json(items_path, processed_items)
    _save_json(latest_dir / "cards_latest.json", cards)

    # Timestamped snapshot
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_dir = DATA_ROOT / source_dir / date_str
    _save_json(date_dir / f"content_items_{ts}.json", processed_items)
    _save_json(date_dir / f"cards_{ts}.json", cards)

    print(f"  Wrote {len(processed_items)} items + cards to JSON")

    # Write to Supabase
    _upsert_to_supabase(processed_items, cards)

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
        help="Preview output without writing files or database",
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
