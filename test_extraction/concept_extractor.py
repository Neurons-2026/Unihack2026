"""
Concept Extractor - Uses Google Gemini LLM to extract key innovative concepts
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

from google import genai

logger = logging.getLogger(__name__)

# Truncate input text to stay within context limits.
# ~20k chars covers title, abstract, intro, and method sections.
MAX_INPUT_CHARS = 20_000

EXTRACTION_PROMPT = """\
You are an expert AI/ML research analyst. Given a source document (either a research paper or a GitHub repository), extract the key concepts that make this work innovative and trending.

For each concept, provide:
1. **label**: A concise, normalized concept name (lowercase, 2-5 words). This will become a node in a knowledge graph.
2. **description**: A one-sentence plain-English explanation of this concept that a non-expert can understand.
3. **why_innovative**: One sentence explaining why this concept is novel, impactful, or trending in the AI landscape.
4. **category**: Classify into one of: "technique", "architecture", "application", "dataset", "tool", "benchmark", "theory".
5. **relevance_score**: A float from 0.0 to 1.0 indicating how central this concept is to the source's innovation (1.0 = the core contribution).

Rules:
- Extract at least 3 and at most 8 concepts per source.
- Focus on what makes this work INNOVATIVE and TRENDING, not generic background concepts.
- Prefer specific technical concepts (e.g., "1-bit quantized inference") over vague ones (e.g., "machine learning").
- For papers: focus on the novel method, key technical insight, and main application domain.
- For GitHub repos: focus on the core capability, key differentiator, and target use case.
- Ensure concept labels are suitable as knowledge graph nodes (concise, specific, lowercase).

Respond ONLY with a valid JSON object in this exact format:
{
  "source_title": "<title of the paper or repo>",
  "source_type": "<pdf or github_repo>",
  "concepts": [
    {
      "label": "concept name",
      "description": "Plain-English explanation.",
      "why_innovative": "Why this is novel/trending.",
      "category": "technique",
      "relevance_score": 0.95
    }
  ]
}
"""

BATCH_EXTRACTION_PROMPT = """\
You are an expert AI/ML research analyst. You will be given MULTIPLE source documents (research papers and/or GitHub repositories), each separated by "=== SOURCE N ===". For EACH source, extract the key concepts that make it innovative and trending.

For each concept, provide:
1. **label**: A concise, normalized concept name (lowercase, 2-5 words). This will become a node in a knowledge graph.
2. **description**: A one-sentence plain-English explanation of this concept that a non-expert can understand.
3. **why_innovative**: One sentence explaining why this concept is novel, impactful, or trending in the AI landscape.
4. **category**: Classify into one of: "technique", "architecture", "application", "dataset", "tool", "benchmark", "theory".
5. **relevance_score**: A float from 0.0 to 1.0 indicating how central this concept is to the source's innovation (1.0 = the core contribution).

Rules:
- Extract at least 3 and at most 8 concepts PER source.
- Focus on what makes each work INNOVATIVE and TRENDING, not generic background concepts.
- Prefer specific technical concepts over vague ones.
- Ensure concept labels are suitable as knowledge graph nodes (concise, specific, lowercase).

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
          "description": "Plain-English explanation.",
          "why_innovative": "Why this is novel/trending.",
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
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API")
    )
    if not key:
        raise ValueError(
            "No API key. Set GEMINI_API_KEY or GOOGLE_API env var, or pass --api-key."
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


def _call_gemini(client, model: str, prompt: str, max_retries: int = 3) -> str:
    """Call Gemini API with retry logic for rate limits."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            return _strip_code_fences(response.text)
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait = 60 * (attempt + 1)
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{max_retries}). "
                    f"Waiting {wait}s before retry..."
                )
                time.sleep(wait)
            else:
                raise


def _parse_concepts(concepts_raw: list[dict]) -> list[ExtractedConcept]:
    """Parse raw concept dicts into ExtractedConcept dataclasses."""
    return [
        ExtractedConcept(
            label=c["label"].lower().strip(),
            description=c["description"],
            why_innovative=c["why_innovative"],
            category=c["category"],
            relevance_score=float(c["relevance_score"]),
        )
        for c in concepts_raw
    ]


def extract_concepts(
    text: str,
    source_file: str,
    model: str = "gemini-2.5-flash-preview-05-20",
    api_key: str | None = None,
) -> ExtractionResult:
    """
    Extract key innovative concepts from a single processed text using Gemini.

    Args:
        text: The processed text content from a paper or GitHub repo.
        source_file: Filename of the source (for metadata).
        model: Gemini model to use.
        api_key: Google AI API key.

    Returns:
        ExtractionResult with source metadata and list of extracted concepts.
    """
    key = _get_api_key(api_key)
    client = genai.Client(api_key=key)
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

    response_text = _call_gemini(client, model, prompt)
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
    model: str = "gemini-2.5-flash-preview-05-20",
    api_key: str | None = None,
) -> list[ExtractionResult]:
    """
    Extract concepts from multiple files in a single LLM call.

    Args:
        file_texts: List of (filename, text_content) tuples.
        model: Gemini model to use.
        api_key: Google AI API key.

    Returns:
        List of ExtractionResult, one per input file.
    """
    key = _get_api_key(api_key)
    client = genai.Client(api_key=key)

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

    response_text = _call_gemini(client, model, prompt)
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
    model: str = "gemini-2.5-flash-preview-05-20",
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
