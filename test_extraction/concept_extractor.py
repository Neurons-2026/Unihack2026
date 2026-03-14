"""
Concept Extractor - Uses Anthropic Claude to extract key innovative concepts
from processed text (papers and GitHub repos).

Produces structured JSON output aligned with the knowledge graph node schema,
identifying at least 3 core concepts per source that make it innovative/trending.
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import anthropic

logger = logging.getLogger(__name__)

# Truncate input text to stay within context limits.
# ~20k chars covers title, abstract, intro, and method sections.
MAX_INPUT_CHARS = 20_000

EXTRACTION_PROMPT = """\
You are an expert AI/ML research analyst. Given a source document (either a research paper or a GitHub repository), extract the key concepts that make this work innovative and trending.

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
- For papers: focus on the novel method, key technical insight, and main application domain.
- For GitHub repos: focus on the core capability, key differentiator, and target use case.

Respond ONLY with a valid JSON object in this exact format:
{
  "source_title": "<title of the paper or repo>",
  "source_type": "<pdf or github_repo>",
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

BATCH_EXTRACTION_PROMPT = """\
You are an expert AI/ML research analyst. You will be given MULTIPLE source documents (research papers and/or GitHub repositories), each separated by "=== SOURCE N ===". For EACH source, extract the key concepts that make it innovative and trending.

For each concept, provide:
1. **label**: A short, precise technical concept name (2-5 words max). It should name a concrete structure, method, formula, or mechanism — e.g., "KL divergence", "rotary position embedding", "mixture of experts". Keep it short: just the core concept name, do NOT append qualifiers like "for X" or "with Y".
2. **description**: A one-sentence explanation in simple, everyday language that someone with NO AI background can understand. Avoid jargon — if you must use a technical term, briefly explain it in parentheses.
3. **why_innovative**: One sentence in plain, accessible language explaining why this concept matters and what real-world impact it has.
4. **impact_on_applications**: One or two sentences in plain, non-technical language explaining how this concept could change or improve real-world products, services, or everyday tools that people already use.
5. **category**: Classify into one of: "technique", "architecture", "application", "dataset", "tool", "benchmark", "theory".
6. **relevance_score**: A float from 0.0 to 1.0 indicating how central this concept is to the source's innovation (1.0 = the core contribution). Only include concepts you would rate above 0.8.

Rules:
- Extract at least 3 and at most 8 concepts PER source, but ONLY those with relevance_score > 0.8.
- Focus on what makes each work INNOVATIVE and TRENDING, not generic background concepts.
- Labels MUST be short and specific: mathematical formulas, architectural components, algorithms, or concrete methods. Avoid vague labels.

Respond ONLY with a valid JSON object in this exact format:
{
  "sources": [
    {
      "source_title": "<title>",
      "source_type": "<pdf or github_repo>",
      "source_file": "<filename>",
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


def _get_api_key(api_key: str | None = None) -> str:
    key = (
        api_key
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ANTHTROPIC_API")
    )
    if not key:
        raise ValueError(
            "No API key. Set ANTHROPIC_API_KEY or ANTHTROPIC_API env var, or pass --api-key."
        )
    return key


def _truncate_text(text: str, max_chars: int = MAX_INPUT_CHARS) -> str:
    """Truncate text to max_chars, preserving the beginning (title, abstract)."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_para = truncated.rfind("\n\n")
    if last_para > max_chars * 0.8:
        truncated = truncated[:last_para]
    return truncated + "\n\n[... truncated for processing ...]"


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences from LLM response to get raw JSON."""
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


def _call_claude(client: anthropic.Anthropic, model: str, prompt: str, max_retries: int = 3) -> str:
    """Call Claude API with retry logic for rate limits."""
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            return _strip_code_fences(message.content[0].text)
        except anthropic.RateLimitError:
            if attempt < max_retries - 1:
                wait = 60 * (attempt + 1)
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{max_retries}). "
                    f"Waiting {wait}s before retry..."
                )
                time.sleep(wait)
            else:
                raise


def _parse_concepts(concepts_raw: list[dict], min_relevance: float = 0.8) -> list[ExtractedConcept]:
    """Parse raw concept dicts into ExtractedConcept dataclasses, filtering by relevance."""
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


def extract_concepts(
    text: str,
    source_file: str,
    model: str = "claude-sonnet-4-6",
    api_key: str | None = None,
) -> ExtractionResult:
    """
    Extract key innovative concepts from a single processed text using Claude.

    Args:
        text: The processed text content from a paper or GitHub repo.
        source_file: Filename of the source (for metadata).
        model: Claude model to use.
        api_key: Anthropic API key.

    Returns:
        ExtractionResult with source metadata and list of extracted concepts.
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
        f"{truncated_text}"
    )

    response_text = _call_claude(client, model, prompt)
    # Fix trailing commas before closing brackets (common LLM JSON issue)
    response_text = re.sub(r",\s*([}\]])", r"\1", response_text)
    parsed = json.loads(response_text)

    concepts = _parse_concepts(parsed["concepts"])

    result = ExtractionResult(
        source_file=source_file,
        source_title=parsed.get("source_title", source_file),
        source_type=parsed.get("source_type", "unknown"),
        concepts=concepts,
    )

    logger.info(
        f"Extracted {len(concepts)} concepts from {source_file}: "
        f"{[c.label for c in concepts]}"
    )

    return result


def extract_concepts_batch(
    file_texts: list[tuple[str, str]],
    model: str = "claude-sonnet-4-6",
    api_key: str | None = None,
) -> list[ExtractionResult]:
    """
    Extract concepts from multiple files in a single LLM call.

    Args:
        file_texts: List of (filename, text_content) tuples.
        model: Claude model to use.
        api_key: Anthropic API key.

    Returns:
        List of ExtractionResult, one per input file.
    """
    key = _get_api_key(api_key)
    client = anthropic.Anthropic(api_key=key)

    # Build combined prompt with all sources
    source_sections = []
    for i, (filename, text) in enumerate(file_texts, 1):
        truncated = _truncate_text(text)
        source_sections.append(
            f"=== SOURCE {i} (file: {filename}) ===\n\n{truncated}"
        )

    combined_text = "\n\n".join(source_sections)
    total_chars = len(combined_text)

    logger.info(
        f"Batch request: {len(file_texts)} sources, "
        f"{total_chars} total chars -> {model}"
    )

    prompt = (
        f"{BATCH_EXTRACTION_PROMPT}\n\n"
        f"--- SOURCE DOCUMENTS ---\n\n"
        f"{combined_text}"
    )

    response_text = _call_claude(client, model, prompt)
    response_text = re.sub(r",\s*([}\]])", r"\1", response_text)
    parsed = json.loads(response_text)

    results = []
    for source_data in parsed["sources"]:
        concepts = _parse_concepts(source_data["concepts"])
        result = ExtractionResult(
            source_file=source_data.get("source_file", ""),
            source_title=source_data.get("source_title", ""),
            source_type=source_data.get("source_type", "unknown"),
            concepts=concepts,
        )
        logger.info(
            f"Extracted {len(concepts)} concepts from {result.source_file}: "
            f"{[c.label for c in concepts]}"
        )
        results.append(result)

    return results


def extract_concepts_from_file(
    file_path: str,
    model: str = "claude-sonnet-4-6",
    api_key: str | None = None,
) -> ExtractionResult:
    """Read a processed text file and extract concepts."""
    path = Path(file_path)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    return extract_concepts(
        text=text,
        source_file=path.name,
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
