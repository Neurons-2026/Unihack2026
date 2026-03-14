"""
Concept extraction API routes.

Endpoints:
  POST /api/v1/concepts/extract-pdf      Upload a PDF and extract concepts
  POST /api/v1/concepts/extract-all      Process all scraped PDFs
  GET  /api/v1/concepts                  List all extracted concept files
  GET  /api/v1/concepts/{paper_id}       Get concepts for a specific paper
"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from services.concept_extraction import (
    CONCEPTS_DIR,
    process_all_pdfs,
    process_pdf_bytes,
    result_to_dict,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/concepts/extract-pdf")
async def extract_from_pdf(
    file: UploadFile = File(...),
    model: str = Query("claude-sonnet-4-6", description="Claude model to use"),
    save: bool = Query(True, description="Save result to backend/data/concepts/"),
):
    """Upload a PDF and extract innovative concepts from it."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        result = process_pdf_bytes(
            pdf_bytes=pdf_bytes,
            filename=file.filename,
            model=model,
            save=save,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to extract concepts from {file.filename}")
        raise HTTPException(
            status_code=500,
            detail=f"Concept extraction failed: {e}",
        )

    return result_to_dict(result)


@router.post("/concepts/extract-all")
async def extract_all(
    model: str = Query("claude-sonnet-4-6", description="Claude model to use"),
    skip_existing: bool = Query(True, description="Skip PDFs with existing concepts"),
):
    """Process all scraped PDFs in backend/data/scraped/pdfs/huggingface/."""
    try:
        results = process_all_pdfs(
            model=model,
            skip_existing=skip_existing,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Failed to process PDFs")
        raise HTTPException(status_code=500, detail=f"Batch extraction failed: {e}")

    return {
        "processed": len(results),
        "total_concepts": sum(len(r.concepts) for r in results),
        "results": [result_to_dict(r) for r in results],
    }


@router.get("/concepts")
async def list_concepts():
    """List all extracted concept files."""
    CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(CONCEPTS_DIR.glob("*_concepts.json"))

    items = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        items.append({
            "file": f.name,
            "source_file": data.get("source_file", ""),
            "source_title": data.get("source_title", ""),
            "num_concepts": len(data.get("concepts", [])),
        })

    return {"count": len(items), "items": items}


@router.get("/concepts/{paper_id}")
async def get_concepts(paper_id: str):
    """Get extracted concepts for a specific paper (by arxiv ID or stem name)."""
    concept_file = CONCEPTS_DIR / f"{paper_id}_concepts.json"
    if not concept_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No concepts found for '{paper_id}'. "
            f"Run extraction first via POST /concepts/extract-all or /concepts/extract-pdf.",
        )

    with open(concept_file, "r", encoding="utf-8") as f:
        return json.load(f)
