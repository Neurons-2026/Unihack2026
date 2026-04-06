"""
Full ingestion pipeline: Scrape → Preprocess → Extract Concepts → Generate Cards → Store to DB.

Orchestrates existing services into a single end-to-end flow.
Concepts are extracted first so that card generation can use concept labels as keywords.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.scrapers.github_trending import scrape_github_trending
from services.scrapers.huggingface_papers import scrape_huggingface_papers
from services.scrapers.anthropic_news import scrape_anthropic_news
from services.scrapers.openai_news import scrape_openai_news
from services.preprocessing import (
    preprocess_item,
    build_text_views,
    clean_by_source,
)
from services.enrichment import enrich_if_needed
from services.card_generation import generate_card_fields
from services.concept_extraction import (
    process_pdf,
    extract_concepts_from_content_item,
    result_to_dict,
    save_result,
    CONCEPTS_DIR,
)
from services.knowledge_graph import (
    build_graph_from_concepts,
    extend_graph_with_concepts,
)

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
SCRAPED_DIR = DATA_DIR / "scraped"


# ---------------------------------------------------------------------------
# Step 1: Scrape all sources
# ---------------------------------------------------------------------------

def _normalize_blog_items(
    raw_items: list[dict[str, Any]],
    source: str,
    collector: str,
) -> list[dict[str, Any]]:
    """Convert simple blog scraper output (url/title/raw_text/date) to content_item schema."""
    output = []
    for rank, item in enumerate(raw_items, start=1):
        url = item.get("url", "")
        slug = url.rstrip("/").split("/")[-1] if url else f"item-{rank}"
        raw_text = item.get("raw_text", "")
        cleaned_text, preview_text = build_text_views(raw_text)

        output.append({
            "schema_version": "1.0.0",
            "id": f"{source}:{slug}",
            "source": source,
            "source_url": url,
            "title": item.get("title", ""),
            "raw_summary": "",
            "raw_content": raw_text,
            "pipeline_state": "raw_scraped",
            "preprocessing": {
                "cleaned_text": cleaned_text,
                "preview_text": preview_text,
                "quality_notes": [],
                "enrichment_used": False,
            },
            "ranking": {
                "source_rank_score": max(0.0, (len(raw_items) - rank + 1) / max(1, len(raw_items))),
                "trending_score": max(0.0, (len(raw_items) - rank + 1) / max(1, len(raw_items))),
            },
            "metadata": {
                "published_date": item.get("date", ""),
                "rank": rank,
                "keywords": [],
                "freshness_basis": "news_listing_order",
            },
            "provenance": {
                "collector": collector,
                "collector_version": "0.2.0",
                "dedupe_key": f"{source}:{slug}",
            },
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })
    return output


def scrape_all_sources(
    github_limit: int = 10,
    hf_limit: int = 10,
    anthropic_limit: int = 5,
    openai_limit: int = 5,
    download_pdfs: bool = True,
    max_pdf_downloads: int = 5,
    sources: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Scrape all configured sources and return unified content_items.

    Args:
        sources: Optional list to limit which sources to scrape.
                 Valid values: "github", "huggingface", "anthropic", "openai".
                 If None, scrapes all.
    """
    allowed = set(sources) if sources else {"github", "huggingface", "anthropic", "openai"}
    all_items: list[dict[str, Any]] = []

    if "github" in allowed:
        logger.info("Scraping GitHub Trending...")
        try:
            github_items = scrape_github_trending(limit=github_limit)
            all_items.extend(github_items)
            logger.info(f"  GitHub: {len(github_items)} items")
        except Exception:
            logger.exception("GitHub scraping failed")

    if "huggingface" in allowed:
        logger.info("Scraping HuggingFace Papers...")
        pdf_dir = SCRAPED_DIR / "pdfs" / "huggingface"
        try:
            hf_items = scrape_huggingface_papers(
                limit=hf_limit,
                download_pdfs=download_pdfs,
                max_pdf_downloads=max_pdf_downloads,
                pdf_dir=pdf_dir,
            )
            all_items.extend(hf_items)
            logger.info(f"  HuggingFace: {len(hf_items)} items")
        except Exception:
            logger.exception("HuggingFace scraping failed")

    if "anthropic" in allowed:
        logger.info("Scraping Anthropic News...")
        try:
            raw = scrape_anthropic_news(n=anthropic_limit)
            items = _normalize_blog_items(raw, "anthropic_blog", "anthropic_news_scraper")
            all_items.extend(items)
            logger.info(f"  Anthropic: {len(items)} items")
        except Exception:
            logger.exception("Anthropic scraping failed")

    if "openai" in allowed:
        logger.info("Scraping OpenAI News...")
        try:
            raw = scrape_openai_news(n=openai_limit)
            items = _normalize_blog_items(raw, "openai_blog", "openai_news_scraper")
            all_items.extend(items)
            logger.info(f"  OpenAI: {len(items)} items")
        except Exception:
            logger.exception("OpenAI scraping failed")

    logger.info(f"Total scraped items: {len(all_items)}")
    return all_items


# ---------------------------------------------------------------------------
# Step 2: Preprocess + Enrich
# ---------------------------------------------------------------------------

def preprocess_all(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run preprocessing and enrichment on all content items."""
    processed = []
    for item in items:
        item = preprocess_item(item)
        item = enrich_if_needed(item)
        processed.append(item)
    logger.info(
        f"Preprocessed {len(processed)} items. "
        f"Enriched: {sum(1 for i in processed if i.get('preprocessing', {}).get('enrichment_used'))}"
    )
    return processed


# ---------------------------------------------------------------------------
# Step 3: Extract concepts from all items (PDFs use full text, others use cleaned text)
# ---------------------------------------------------------------------------

def extract_all_concepts(
    items: list[dict[str, Any]],
    model: str = "claude-sonnet-4-6",
    skip_existing: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    """
    Extract concepts from all content items.

    - Items with PDFs: extract from the full PDF text (richer content).
    - Items without PDFs: extract from preprocessed cleaned_text.

    Returns:
        concept_results: List of concept extraction result dicts.
        concepts_by_item: Mapping of item_id -> list of concept labels.
    """
    concept_results: list[dict[str, Any]] = []
    concepts_by_item: dict[str, list[str]] = {}

    # Only extract concepts from HuggingFace papers — other sources are too short
    # and low-signal to justify the Sonnet API cost.
    hf_items = [item for item in items if item.get("source") == "huggingface"]
    skipped = len(items) - len(hf_items)
    if skipped:
        logger.info(f"Skipping concept extraction for {skipped} non-HuggingFace items")

    for i, item in enumerate(hf_items):
        item_id = item.get("id", "")
        logger.info(
            f"Concept extraction {i + 1}/{len(hf_items)}: {item.get('title', '')[:60]}"
        )

        # Check if this item has a PDF
        pdf_path = (item.get("metadata") or {}).get("pdf_path", "")
        pdf_file = Path(pdf_path) if pdf_path else None

        if pdf_file and pdf_file.exists():
            # PDF available — check if already extracted
            stem = pdf_file.stem
            existing = CONCEPTS_DIR / f"{stem}_concepts.json"
            if skip_existing and existing.exists():
                logger.info(f"  Using cached concepts for {stem}")
                with open(existing, "r", encoding="utf-8") as f:
                    result_dict = json.load(f)
                concept_results.append(result_dict)
                concepts_by_item[item_id] = [
                    c["label"] for c in result_dict.get("concepts", [])
                ]
                continue

            # Extract from PDF
            try:
                result = process_pdf(pdf_file, model=model)
                save_result(result, CONCEPTS_DIR)
                result_dict = result_to_dict(result)
                concept_results.append(result_dict)
                concepts_by_item[item_id] = [c.label for c in result.concepts]
            except Exception:
                logger.exception(f"  PDF concept extraction failed for {pdf_file.name}")
        else:
            # No PDF — extract from preprocessed cleaned_text
            cleaned_text = (item.get("preprocessing") or {}).get("cleaned_text", "")
            if not cleaned_text or len(cleaned_text.split()) < 50:
                logger.info(f"  Skipping {item_id} (text too short for concept extraction)")
                continue

            try:
                result = extract_concepts_from_content_item(item, model=model)
                if result.concepts:
                    result_dict = result_to_dict(result)
                    concept_results.append(result_dict)
                    concepts_by_item[item_id] = [c.label for c in result.concepts]
                    save_result(result, CONCEPTS_DIR)
                else:
                    logger.info(f"  No concepts extracted from {item_id}")
            except Exception:
                logger.exception(f"  Concept extraction failed for {item_id}")

    total_concepts = sum(len(labels) for labels in concepts_by_item.values())
    logger.info(
        f"Concept extraction complete: {len(concept_results)}/{len(hf_items)} HF sources, "
        f"{total_concepts} total concepts"
    )
    return concept_results, concepts_by_item


# ---------------------------------------------------------------------------
# Step 3b: Filter out items already stored in DB (skip Claude calls for dupes)
# ---------------------------------------------------------------------------

def _filter_new_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return only items whose id is not already in the cards table."""
    try:
        from supabase import create_client
        from config import get_settings
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_key:
            return items
        supabase = create_client(settings.supabase_url, settings.supabase_key)
        ids = [item["id"] for item in items]
        result = supabase.table("cards").select("id").in_("id", ids).execute()
        existing_ids = {row["id"] for row in (result.data or [])}
        new_items = [item for item in items if item["id"] not in existing_ids]
        skipped = len(items) - len(new_items)
        if skipped:
            logger.info(f"Skipping {skipped} items already in DB — no Claude calls needed")
        return new_items
    except Exception as exc:
        logger.warning("Could not check existing cards, processing all: %s", exc)
        return items


# ---------------------------------------------------------------------------
# Step 4: Generate card fields via Claude (uses extracted concepts as keywords)
# ---------------------------------------------------------------------------

def generate_cards(
    items: list[dict[str, Any]],
    concepts_by_item: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """Generate card_title, card_summary, keywords, thumbnail_keyword for each item.

    Only processes items that don't already have a card in the DB.
    Uses extracted concept labels as required keywords for each card.
    """
    concepts_by_item = concepts_by_item or {}
    new_items = _filter_new_items(items)

    for i, item in enumerate(new_items):
        item_id = item.get("id", "")
        concept_labels = concepts_by_item.get(item_id)
        logger.info(
            f"Generating card {i + 1}/{len(new_items)}: {item.get('title', '')[:60]}"
            f"{f' (concepts: {concept_labels})' if concept_labels else ''}"
        )
        try:
            generate_card_fields(item, concept_labels=concept_labels)
            item["pipeline_state"] = "card_ready"
        except Exception:
            logger.exception(f"Card generation failed for {item_id}")

    # Mark already-existing items as card_ready so they still get stored/returned
    new_ids = {item["id"] for item in new_items}
    for item in items:
        if item["id"] not in new_ids:
            item["pipeline_state"] = "card_ready"

    ready = sum(1 for i in items if i.get("pipeline_state") == "card_ready")
    logger.info(f"Card generation complete: {ready}/{len(items)} ready ({len(new_items)} newly generated)")
    return items


# ---------------------------------------------------------------------------
# Step 5: Store to Supabase
# ---------------------------------------------------------------------------

def store_to_database(
    items: list[dict[str, Any]],
    concept_results: list[dict[str, Any]],
) -> dict[str, int]:
    """
    Store processed items to Supabase tables.

    Actual DB schema:
      content_items: id, schema_version, source, source_url, title, raw_summary,
                     raw_content, metadata, fetched_at, published_at, provenance
      cards:         id, card_title, card_summary, keywords, thumbnail_keyword,
                     cleaned_text, quality_score, trending_score, image_url
      graph_nodes:   id, label, description, frequency
      graph_edges:   id(auto), source_node_id, target_node_id, relationship, weight

    Returns counts of rows upserted to each table.
    """
    from supabase import create_client
    from config import get_settings

    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        logger.warning("No Supabase credentials — skipping database storage")
        return {"content_items": 0, "cards": 0, "graph_nodes": 0, "graph_edges": 0}

    supabase = create_client(settings.supabase_url, settings.supabase_key)
    counts: dict[str, int] = {}

    # --- content_items table ---
    content_rows = []
    for item in items:
        preprocessing = item.get("preprocessing") or {}
        content_rows.append({
            "id": item["id"],
            "source": item.get("source", ""),
            "source_url": item.get("source_url", ""),
            "title": item.get("title", ""),
            "raw_content": item.get("raw_content", ""),
            "cleaned_text": preprocessing.get("cleaned_text", ""),
            "preview_text": preprocessing.get("preview_text", ""),
            "quality_score": preprocessing.get("quality_score"),
            "quality_notes": preprocessing.get("quality_notes") or [],
            "enrichment_used": bool(preprocessing.get("enrichment_used", False)),
            "keywords": item.get("metadata", {}).get("keywords") or [],
            "pipeline_state": item.get("pipeline_state", "raw_scraped"),
            "fetched_at": item.get("fetched_at"),
        })

    if content_rows:
        try:
            resp = supabase.table("content_items").upsert(content_rows, on_conflict="id").execute()
            counts["content_items"] = len(resp.data or [])
            logger.info(f"Upserted {counts['content_items']} content_items")
        except Exception:
            logger.exception("Failed to upsert content_items")
            counts["content_items"] = 0

    # --- cards table ---
    card_rows = []
    for item in items:
        card = item.get("card")
        if not card:
            continue
        ranking = item.get("ranking", {})
        card_rows.append({
            "id": item["id"],
            "card_title": card.get("card_title", ""),
            "card_summary": card.get("card_summary", ""),
            "keywords": card.get("keywords", []),
            "source": item.get("source", ""),
            "source_url": item.get("source_url", ""),
            "thumbnail_keyword": card.get("thumbnail_keyword", ""),
            "trending_score": ranking.get("trending_score", 0.0),
            "image_url": card.get("image_url", ""),
        })

    if card_rows:
        try:
            resp = supabase.table("cards").upsert(card_rows, on_conflict="id").execute()
            counts["cards"] = len(resp.data or [])
            logger.info(f"Upserted {counts['cards']} cards")
        except Exception:
            logger.exception("Failed to upsert cards")
            counts["cards"] = 0

    # --- graph_nodes + graph_edges (from extracted concepts) ---
    if concept_results:
        try:
            graph_nodes, graph_edges = build_graph_from_concepts(concept_results)

            node_rows = [
                {
                    "id": n.id,
                    "label": n.label,
                    "description": n.description or "",
                    "frequency": n.frequency or 1,
                }
                for n in graph_nodes
            ]
            if node_rows:
                resp = supabase.table("graph_nodes").upsert(node_rows, on_conflict="id").execute()
                counts["graph_nodes"] = len(resp.data or [])
                logger.info(f"Upserted {counts['graph_nodes']} graph_nodes")

            edge_rows = [
                {
                    "id": f"{e.source_node_id}__{e.target_node_id}__{e.relationship or 'related_to'}",
                    "source_node_id": e.source_node_id,
                    "target_node_id": e.target_node_id,
                    "relationship": e.relationship or "related_to",
                    "weight": e.weight or 1.0,
                }
                for e in graph_edges
            ]
            if edge_rows:
                resp = supabase.table("graph_edges").upsert(edge_rows, on_conflict="id").execute()
                counts["graph_edges"] = len(resp.data or [])
                logger.info(f"Upserted {counts['graph_edges']} graph_edges")
        except Exception:
            logger.exception("Failed to build/store knowledge graph")
            counts.setdefault("graph_nodes", 0)
            counts.setdefault("graph_edges", 0)

    return counts


# ---------------------------------------------------------------------------
# Step 6: Save locally (always runs, DB is optional)
# ---------------------------------------------------------------------------

def save_locally(
    items: list[dict[str, Any]],
    concept_results: list[dict[str, Any]],
) -> Path:
    """Save all pipeline output to a timestamped local directory."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    date_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run_dir = SCRAPED_DIR / "pipeline_runs" / date_key
    run_dir.mkdir(parents=True, exist_ok=True)

    # Content items
    content_path = run_dir / f"content_items_{stamp}.json"
    content_path.write_text(
        json.dumps(items, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    # Cards
    cards = [
        {
            "id": item["id"],
            **(item.get("card") or {}),
            "source": item.get("source", ""),
            "source_url": item.get("source_url", ""),
            "trending_score": (item.get("ranking") or {}).get("trending_score", 0.0),
        }
        for item in items
        if item.get("card")
    ]
    cards_path = run_dir / f"cards_{stamp}.json"
    cards_path.write_text(
        json.dumps(cards, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Concepts summary
    if concept_results:
        concepts_path = run_dir / f"concepts_{stamp}.json"
        concepts_path.write_text(
            json.dumps(concept_results, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    logger.info(f"Saved pipeline output to {run_dir}")
    return run_dir


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    sources: list[str] | None = None,
    generate_cards_flag: bool = True,
    extract_concepts_flag: bool = True,
    store_to_db: bool = True,
    model: str = "claude-sonnet-4-6",
) -> dict[str, Any]:
    """
    Run the full ingestion pipeline end-to-end.

    Args:
        sources: Which sources to scrape (None = all).
        generate_cards_flag: Whether to generate card fields via Claude.
        extract_concepts_flag: Whether to extract concepts from PDFs.
        store_to_db: Whether to store results in Supabase.
        model: Claude model for concept extraction.

    Returns:
        Summary dict with counts and output paths.
    """
    logger.info("=" * 60)
    logger.info("Starting full ingestion pipeline")
    logger.info("=" * 60)

    # Step 1: Scrape
    items = scrape_all_sources(sources=sources)

    # Step 2: Preprocess + enrich
    items = preprocess_all(items)

    # Step 3: Extract concepts (before card generation so concepts feed into keywords)
    concept_results = []
    concepts_by_item: dict[str, list[str]] = {}
    if extract_concepts_flag:
        concept_results, concepts_by_item = extract_all_concepts(items, model=model)

    # Step 4: Generate card fields (uses extracted concept labels as keywords)
    if generate_cards_flag:
        items = generate_cards(items, concepts_by_item=concepts_by_item)

    # Step 5: Save locally (always)
    run_dir = save_locally(items, concept_results)

    # Step 6: Store to DB (optional)
    db_counts = {}
    if store_to_db:
        db_counts = store_to_database(items, concept_results)

    summary = {
        "scraped": len(items),
        "cards_generated": sum(1 for i in items if i.get("card")),
        "concepts_extracted": len(concept_results),
        "total_concepts": sum(len(r.get("concepts", [])) for r in concept_results),
        "local_output": str(run_dir),
        "db_counts": db_counts,
    }

    logger.info("=" * 60)
    logger.info("Pipeline complete!")
    for k, v in summary.items():
        logger.info(f"  {k}: {v}")
    logger.info("=" * 60)

    return summary
