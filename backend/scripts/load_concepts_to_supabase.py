"""
Load extracted concept JSON into Supabase `graph_nodes`.

Usage:
    python backend/scripts/load_concepts_to_supabase.py \
      --file backend/data/concepts/2603.12180_concepts.json

Optional:
    --dry-run     Print rows without writing to Supabase
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

from supabase import Client, create_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


def _load_env_file(path: Path) -> int:
    if not path.exists():
        return 0

    loaded = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue

        os.environ[key] = value
        loaded += 1

    return loaded


def get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY", "")
    if not supabase_url or not supabase_key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in environment")

    if supabase_key.startswith("sb_publishable_"):
        raise RuntimeError(
            "SUPABASE_KEY is a publishable key. Use the backend service-role key "
            "(legacy JWT) from Supabase Settings -> API."
        )

    return create_client(supabase_url, supabase_key)


def _normalize_id(label: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", label.lower().strip())
    return normalized.strip("_") or "concept"


def _build_description(concept: dict[str, Any], source_title: str, source_file: str) -> str:
    description = concept.get("description", "").strip()
    why_innovative = concept.get("why_innovative", "").strip()
    impact_on_applications = concept.get("impact_on_applications", "").strip()
    category = concept.get("category", "").strip()
    relevance_score = concept.get("relevance_score", 0)

    return (
        f"{description}\n\n"
        f"Why innovative: {why_innovative}\n"
        f"Impact: {impact_on_applications}\n"
        f"Category: {category}\n"
        f"Relevance: {relevance_score}\n"
        f"Source: {source_title} ({source_file})"
    )


def _rows_from_concepts(payload: dict[str, Any]) -> list[dict[str, Any]]:
    source_title = payload.get("source_title", "Unknown Source")
    source_file = payload.get("source_file", "unknown.pdf")
    concepts = payload.get("concepts", [])

    rows: list[dict[str, Any]] = []
    for concept in concepts:
        label = str(concept.get("label", "")).strip()
        if not label:
            continue

        rows.append(
            {
                "id": _normalize_id(label),
                "label": label,
                "description": _build_description(concept, source_title, source_file),
                "frequency": 1,
            }
        )

    return rows


def load_concepts(concept_file: Path, dry_run: bool = False) -> int:
    payload = json.loads(concept_file.read_text(encoding="utf-8"))
    rows = _rows_from_concepts(payload)

    if not rows:
        logger.warning("No concepts found in %s", concept_file)
        return 0

    logger.info("Prepared %d concept rows from %s", len(rows), concept_file.name)

    if dry_run:
        for row in rows:
            logger.info("DRY RUN -> %s", row)
        return len(rows)

    supabase = get_supabase_client()
    response = supabase.table("graph_nodes").upsert(rows, on_conflict="id").execute()
    inserted_count = len(response.data or [])

    logger.info("Upserted %d rows into graph_nodes", inserted_count)
    return inserted_count


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    root_loaded = _load_env_file(PROJECT_ROOT / ".env")
    backend_loaded = _load_env_file(BACKEND_ROOT / ".env")
    logger.info(
        "Loaded %d vars from root .env and %d vars from backend .env",
        root_loaded,
        backend_loaded,
    )

    parser = argparse.ArgumentParser(description="Load concept JSON into Supabase graph_nodes")
    parser.add_argument(
        "--file",
        default=str(BACKEND_ROOT / "data" / "concepts" / "2603.12180_concepts.json"),
        help="Path to concept JSON file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write to Supabase; only print what would be inserted",
    )
    args = parser.parse_args()

    concept_file = Path(args.file)
    if not concept_file.exists():
        raise FileNotFoundError(f"Concept file not found: {concept_file}")

    inserted = load_concepts(concept_file=concept_file, dry_run=args.dry_run)
    logger.info("Done. Rows processed: %d", inserted)


if __name__ == "__main__":
    main()
