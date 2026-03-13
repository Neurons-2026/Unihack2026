"""
Concept Extractor - Uses Google Gemini LLM to extract key innovative concepts
from processed text (papers and GitHub repos).

Produces structured JSON output aligned with the knowledge graph node schema,
identifying at least 3 core concepts per source that make it innovative/trending.
"""

import json
import logging
import os
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


def extract_concepts(
    text: str,
    source_file: str,
    model: str = "gemini-2.0-flash",
    api_key: str | None = None,
) -> ExtractionResult:
    """
    Extract key innovative concepts from processed text using Google Gemini.

    Args:
        text: The processed text content from a paper or GitHub repo.
        source_file: Filename of the source (for metadata).
        model: Gemini model to use (default: gemini-2.0-flash, free tier).
        api_key: Google AI API key. Falls back to GEMINI_API_KEY env var.

    Returns:
        ExtractionResult with source metadata and list of extracted concepts.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "No API key. Set GEMINI_API_KEY env var or pass --api-key."
        )

    client = genai.Client(api_key=key)

    truncated_text = _truncate_text(text)

    logger.info(
        f"Sending {len(truncated_text)} chars to {model} for concept extraction "
        f"(source: {source_file})"
    )

    prompt = (
        f"{EXTRACTION_PROMPT}\n\n"
        f"--- SOURCE DOCUMENT ---\n\n"
        f"{truncated_text}"
    )

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    response_text = _strip_code_fences(response.text)
    parsed = json.loads(response_text)

    concepts = [
        ExtractedConcept(
            label=c["label"].lower().strip(),
            description=c["description"],
            why_innovative=c["why_innovative"],
            category=c["category"],
            relevance_score=float(c["relevance_score"]),
        )
        for c in parsed["concepts"]
    ]

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


def extract_concepts_from_file(
    file_path: str,
    model: str = "gemini-2.0-flash",
    api_key: str | None = None,
) -> ExtractionResult:
    """
    Read a processed text file and extract concepts.

    Args:
        file_path: Path to the processed .txt file.
        model: Gemini model to use.
        api_key: Google AI API key.

    Returns:
        ExtractionResult with extracted concepts.
    """
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
