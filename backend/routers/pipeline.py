"""
Pipeline API route — trigger the full ingestion pipeline via HTTP.

POST /api/v1/pipeline/run
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query

from services.pipeline import run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/pipeline/run")
async def trigger_pipeline(
    sources: Optional[str] = Query(
        None,
        description="Comma-separated sources to scrape (github,huggingface,anthropic,openai). Default: all.",
    ),
    generate_cards: bool = Query(True, description="Generate card fields via Claude"),
    extract_concepts: bool = Query(True, description="Extract concepts from PDFs"),
    store_to_db: bool = Query(True, description="Store results in Supabase"),
    model: str = Query("claude-sonnet-4-6", description="Claude model for concept extraction"),
):
    """Run the full ingestion pipeline: Scrape → Preprocess → Cards → Concepts → DB."""
    source_list = [s.strip() for s in sources.split(",")] if sources else None

    summary = run_pipeline(
        sources=source_list,
        generate_cards_flag=generate_cards,
        extract_concepts_flag=extract_concepts,
        store_to_db=store_to_db,
        model=model,
    )

    return summary
