"""
Concept Extraction Service — Processes scraped PDFs and extracts key innovative
concepts using Claude, producing one JSON file per paper.

Reads PDFs from: backend/data/scraped/pdfs/huggingface/
Writes concepts to: backend/data/concepts/
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import anthropic
import pdfplumber

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = BACKEND_DIR / "data" / "scraped" / "pdfs" / "huggingface"
CONCEPTS_DIR = BACKEND_DIR / "data" / "concepts"

MAX_INPUT_CHARS = 20_000

EXTRACTION_PROMPT = """\
You are an expert AI/ML research analyst. Given a source document (a research paper), extract the key concepts that make this work innovative and trending.

For each concept, provide:
1. **label**: A short, precise technical concept name (2-5 words max). It should name a concrete structure, method, formula, or mechanism — e.g., "KL divergence", "rotary position embedding", "mixture of experts", "flash attention", "low-rank adaptation". Keep it short: just the core concept name, do NOT append qualifiers like "for X" or "with Y".
2. **description**: A one-sentence explanation in simple, everyday language that someone with NO AI background can understand. Avoid jargon — if you must use a technical term, briefly explain it in parentheses.
3. **why_innovative**: One sentence in plain, accessible language explaining why this concept matters and what real-world impact it has. Focus on the "so what?" — what does this enable that wasn't possible before?
4. **impact_on_applications**: One or two sentences in plain, non-technical language explaining how this concept could change or improve real-world products, services, or everyday tools that people already use. Think about concrete examples — e.g., "This could make voice assistants on your phone respond faster and more accurately" or "This could help doctors spot diseases in medical scans that are easy to miss."
5. **category**: Classify into one of: "technique", "architecture", "application", "dataset", "tool", "benchmark", "theory".
6. **relevance_score**: A float from 0.0 to 1.0 indicating how central this concept is to the source's innovation (1.0 = the core contribution). Only include concepts you would rate above 0.8.

Rules:
- Extract at least 3 and at most 8 concepts per source, but ONLY those with relevance_score > 0.8.
- Focus on what makes this work INNOVATIVE and TRENDING, not generic background concepts.
- Labels MUST be short and specific: mathematical formulas (e.g., "KL divergence"), architectural components (e.g., "multi-head attention"), algorithms (e.g., "beam search"), or concrete methods (e.g., "sparse mixture of experts"). Avoid vague labels like "efficiency improvement" or "novel approach".
- Focus on the novel method, key technical insight, and main application domain.

Respond ONLY with a valid JSON object in this exact format:
{
  "source_title": "<title of the paper>",
  "source_type": "pdf",
  "concepts": [
    {
      "label": "concept name",
      "description": "Simple, jargon-free explanation.",
      "why_innovative": "Why this matters in plain language.",
      "impact_on_applications": "How this could improve real-world products or services people use.",
      "category": "technique",
      "relevance_score": 0.95
    }
  ]
}
"""


@dataclass
class ExtractedConcept:
    label: str
    description: str
    why_innovative: str
    impact_on_applications: str
    category: str
    relevance_score: float


@dataclass
class ExtractionResult:
    source_file: str
    source_title: str
    source_type: str
    concepts: list[ExtractedConcept]


# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extract raw text from all pages of a PDF using pdfplumber."""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                pages_text.append(text)
            else:
                logger.warning(f"Page {i + 1} of {pdf_path} yielded no text.")
    return "\n\n".join(pages_text)


def clean_extracted_text(raw_text: str) -> str:
    """Clean raw PDF-extracted text for downstream NLP use."""
    text = raw_text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"\n\s*\d{1,3}\s*\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()


# ---------------------------------------------------------------------------
# Claude concept extraction
# ---------------------------------------------------------------------------

def _get_api_key(api_key: str | None = None) -> str:
    key = (
        api_key
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ANTHTROPIC_API")
    )
    if not key:
        raise ValueError(
            "No Anthropic API key found. "
            "Set ANTHROPIC_API_KEY or ANTHTROPIC_API env var."
        )
    return key


def _truncate_text(text: str, max_chars: int = MAX_INPUT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_para = truncated.rfind("\n\n")
    if last_para > max_chars * 0.8:
        truncated = truncated[:last_para]
    return truncated + "\n\n[... truncated for processing ...]"


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.strip().startswith("```") and not in_block:
                in_block = True
                continue
            elif line.strip() == "```" and in_block:
                break
            elif in_block:
                json_lines.append(line)
        return "\n".join(json_lines)
    return text


def _call_claude(
    client: anthropic.Anthropic,
    model: str,
    prompt: str,
    max_retries: int = 3,
) -> str:
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return _strip_code_fences(message.content[0].text)
        except anthropic.RateLimitError:
            if attempt < max_retries - 1:
                wait = 60 * (attempt + 1)
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{max_retries}). "
                    f"Waiting {wait}s..."
                )
                time.sleep(wait)
            else:
                raise


def _parse_concepts(
    concepts_raw: list[dict],
    min_relevance: float = 0.8,
) -> list[ExtractedConcept]:
    results = []
    for c in concepts_raw:
        score = float(c["relevance_score"])
        if score <= min_relevance:
            continue
        results.append(
            ExtractedConcept(
                label=c["label"].lower().strip(),
                description=c["description"],
                why_innovative=c["why_innovative"],
                impact_on_applications=c.get("impact_on_applications", ""),
                category=c["category"],
                relevance_score=score,
            )
        )
    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_concepts_from_text(
    text: str,
    source_file: str,
    source_type: str = "pdf",
    model: str = "claude-sonnet-4-6",
    api_key: str | None = None,
) -> ExtractionResult:
    """Extract key innovative concepts from text using Claude.

    Works with any preprocessed text — PDF content, blog articles, README text, etc.
    """
    key = _get_api_key(api_key)
    client = anthropic.Anthropic(api_key=key)
    truncated_text = _truncate_text(text)

    logger.info(
        f"Sending {len(truncated_text)} chars to {model} "
        f"(source: {source_file})"
    )

    prompt = (
        f"{EXTRACTION_PROMPT}\n\n"
        f"--- SOURCE DOCUMENT ---\n\n"
        f"SOURCE_TYPE: {source_type}\n"
        f"SOURCE_FILE: {source_file}\n"
        f"---\n\n"
        f"{truncated_text}"
    )

    response_text = _call_claude(client, model, prompt)
    response_text = re.sub(r",\s*([}\]])", r"\1", response_text)
    parsed = json.loads(response_text)

    concepts = _parse_concepts(parsed["concepts"])

    result = ExtractionResult(
        source_file=source_file,
        source_title=parsed.get("source_title", source_file),
        source_type=parsed.get("source_type", source_type),
        concepts=concepts,
    )

    logger.info(
        f"Extracted {len(concepts)} concepts from {source_file}: "
        f"{[c.label for c in concepts]}"
    )
    return result


def extract_concepts_from_content_item(
    item: dict,
    model: str = "claude-sonnet-4-6",
    api_key: str | None = None,
) -> ExtractionResult:
    """
    Extract concepts from a preprocessed content_item dict.

    Uses the item's cleaned_text (from preprocessing) rather than reading a PDF.
    This allows concept extraction from any source (GitHub, blogs, papers, etc.).
    """
    cleaned_text = (item.get("preprocessing") or {}).get("cleaned_text", "")
    if not cleaned_text:
        cleaned_text = item.get("raw_content", "") or item.get("raw_summary", "")

    if not cleaned_text.strip():
        logger.warning(f"No text available for concept extraction: {item.get('id')}")
        return ExtractionResult(
            source_file=item.get("id", "unknown"),
            source_title=item.get("title", "unknown"),
            source_type=item.get("source", "text"),
            concepts=[],
        )

    source_type = "pdf" if item.get("source") == "huggingface" else "article"
    return extract_concepts_from_text(
        text=cleaned_text,
        source_file=item.get("id", "unknown"),
        source_type=source_type,
        model=model,
        api_key=api_key,
    )


def result_to_dict(result: ExtractionResult) -> dict:
    """Convert ExtractionResult to a JSON-serializable dict."""
    return {
        "source_file": result.source_file,
        "source_title": result.source_title,
        "source_type": result.source_type,
        "concepts": [asdict(c) for c in result.concepts],
    }


def process_pdf(
    pdf_path: str | Path,
    model: str = "claude-sonnet-4-6",
    api_key: str | None = None,
) -> ExtractionResult:
    """
    Full pipeline for a single PDF: extract text -> clean -> extract concepts.

    Args:
        pdf_path: Path to the PDF file.
        model: Claude model to use.
        api_key: Anthropic API key (falls back to env vars).

    Returns:
        ExtractionResult with extracted concepts.
    """
    pdf_path = Path(pdf_path)
    logger.info(f"Processing PDF: {pdf_path.name}")

    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text.strip():
        logger.error(f"No text extracted from {pdf_path.name}")
        return ExtractionResult(
            source_file=pdf_path.name,
            source_title=pdf_path.stem,
            source_type="pdf",
            concepts=[],
        )

    cleaned_text = clean_extracted_text(raw_text)
    logger.info(
        f"Extracted {len(cleaned_text)} chars "
        f"(~{len(cleaned_text.split())} words) from {pdf_path.name}"
    )

    return extract_concepts_from_text(
        text=cleaned_text,
        source_file=pdf_path.name,
        model=model,
        api_key=api_key,
    )


def save_result(result: ExtractionResult, output_dir: str | Path) -> Path:
    """Save a single ExtractionResult as JSON."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(result.source_file).stem
    output_path = output_dir / f"{stem}_concepts.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_to_dict(result), f, indent=2, ensure_ascii=False)

    logger.info(f"Saved concepts: {output_path}")
    return output_path


def process_pdf_bytes(
    pdf_bytes: bytes,
    filename: str,
    model: str = "claude-sonnet-4-6",
    api_key: str | None = None,
    save: bool = True,
    output_dir: str | Path | None = None,
) -> ExtractionResult:
    """
    Process raw PDF bytes directly (e.g. from an upload) without needing
    a file on disk. Extracts text, cleans, and runs concept extraction.

    Args:
        pdf_bytes: Raw PDF file content.
        filename: Original filename for metadata.
        model: Claude model to use.
        api_key: Anthropic API key.
        save: Whether to save the result JSON to output_dir.
        output_dir: Directory for concept JSONs (default: backend/data/concepts/).

    Returns:
        ExtractionResult with extracted concepts.
    """
    import io

    logger.info(f"Processing uploaded PDF: {filename} ({len(pdf_bytes)} bytes)")

    pages_text = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                pages_text.append(text)
            else:
                logger.warning(f"Page {i + 1} of {filename} yielded no text.")

    raw_text = "\n\n".join(pages_text)
    if not raw_text.strip():
        logger.error(f"No text extracted from {filename}")
        return ExtractionResult(
            source_file=filename,
            source_title=Path(filename).stem,
            source_type="pdf",
            concepts=[],
        )

    cleaned_text = clean_extracted_text(raw_text)
    logger.info(
        f"Extracted {len(cleaned_text)} chars "
        f"(~{len(cleaned_text.split())} words) from {filename}"
    )

    result = extract_concepts_from_text(
        text=cleaned_text,
        source_file=filename,
        model=model,
        api_key=api_key,
    )

    if save:
        save_result(result, output_dir or CONCEPTS_DIR)

    return result


def process_all_pdfs(
    pdf_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    model: str = "claude-sonnet-4-6",
    api_key: str | None = None,
    skip_existing: bool = True,
) -> list[ExtractionResult]:
    """
    Process all PDFs in pdf_dir and save concept JSONs to output_dir.

    Args:
        pdf_dir: Directory containing PDFs (default: backend/data/scraped/pdfs/huggingface/).
        output_dir: Directory for concept JSONs (default: backend/data/concepts/).
        model: Claude model to use.
        api_key: Anthropic API key.
        skip_existing: Skip PDFs that already have a concept JSON.

    Returns:
        List of ExtractionResult for all processed PDFs.
    """
    pdf_dir = Path(pdf_dir) if pdf_dir else PDF_DIR
    output_dir = Path(output_dir) if output_dir else CONCEPTS_DIR

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDFs found in {pdf_dir}")
        return []

    logger.info(f"Found {len(pdf_files)} PDFs in {pdf_dir}")

    results = []
    for pdf_path in pdf_files:
        stem = pdf_path.stem
        output_path = output_dir / f"{stem}_concepts.json"

        if skip_existing and output_path.exists():
            logger.info(f"Skipping {pdf_path.name} (concepts already exist)")
            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            result = ExtractionResult(
                source_file=data["source_file"],
                source_title=data["source_title"],
                source_type=data["source_type"],
                concepts=[ExtractedConcept(**c) for c in data["concepts"]],
            )
            results.append(result)
            continue

        try:
            result = process_pdf(pdf_path, model=model, api_key=api_key)
            save_result(result, output_dir)
            results.append(result)
        except Exception:
            logger.exception(f"Failed to process {pdf_path.name}")

    logger.info(
        f"Done: {len(results)} PDFs processed, "
        f"concepts saved to {output_dir}"
    )
    return results
