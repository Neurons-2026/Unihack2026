"""
Runner script for concept extraction pipeline.
Processes all text files in resource/processed_test/ and outputs
structured concept JSON to resource/processed_test/concepts/.

Usage:
    python -m test_extraction.run_concept_extraction
    # or
    python test_extraction/run_concept_extraction.py

    # Use a specific model:
    python -m test_extraction.run_concept_extraction --model gemini-2.0-flash

    # Process a single file:
    python -m test_extraction.run_concept_extraction --file trendingPaper1.txt
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from test_extraction.concept_extractor import (
    extract_concepts_from_file,
    result_to_dict,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PROCESSED_DIR = PROJECT_ROOT / "resource" / "processed_test"
CONCEPTS_OUTPUT_DIR = PROCESSED_DIR / "concepts"


def process_single_file(
    file_path: Path, output_dir: Path, model: str, api_key: str | None
) -> dict | None:
    """Process one text file and save concept JSON."""
    output_path = output_dir / f"{file_path.stem}_concepts.json"

    try:
        result = extract_concepts_from_file(
            file_path=str(file_path),
            model=model,
            api_key=api_key,
        )
        result_dict = result_to_dict(result)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"  OK: {file_path.name} -> {output_path.name}")
        logger.info(f"      Concepts: {[c['label'] for c in result_dict['concepts']]}")
        return result_dict

    except Exception as e:
        logger.error(f"  FAIL: {file_path.name}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Extract concepts from processed text")
    parser.add_argument(
        "--model",
        default="gemini-2.0-flash",
        help="Gemini model to use (default: gemini-2.0-flash)",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Process only this specific file (filename, not full path)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Google AI API key (or set GEMINI_API_KEY env var)",
    )
    args = parser.parse_args()

    # Validate API key availability
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error(
            "No API key provided. Set GEMINI_API_KEY env var or use --api-key flag."
        )
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Concept Extraction Pipeline")
    logger.info(f"  Model:      {args.model}")
    logger.info(f"  Input dir:  {PROCESSED_DIR}")
    logger.info(f"  Output dir: {CONCEPTS_OUTPUT_DIR}")
    logger.info("=" * 60)

    CONCEPTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Collect files to process
    if args.file:
        target = PROCESSED_DIR / args.file
        if not target.exists():
            logger.error(f"File not found: {target}")
            sys.exit(1)
        txt_files = [target]
    else:
        txt_files = sorted(
            f for f in PROCESSED_DIR.glob("*.txt") if f.is_file()
        )

    if not txt_files:
        logger.warning("No .txt files found to process.")
        sys.exit(0)

    logger.info(f"Processing {len(txt_files)} file(s)...\n")

    all_results = []
    for txt_file in txt_files:
        result = process_single_file(txt_file, CONCEPTS_OUTPUT_DIR, args.model, api_key)
        if result:
            all_results.append(result)

    # Write combined summary
    if all_results:
        summary_path = CONCEPTS_OUTPUT_DIR / "all_concepts_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        logger.info(f"\nCombined summary saved to: {summary_path}")

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("Extraction complete!")
    logger.info(f"  Files processed: {len(all_results)} / {len(txt_files)}")

    total_concepts = sum(len(r["concepts"]) for r in all_results)
    logger.info(f"  Total concepts extracted: {total_concepts}")

    if all_results:
        logger.info("\n  Per-source breakdown:")
        for r in all_results:
            logger.info(f"    {r['source_file']}:")
            logger.info(f"      Title: {r['source_title']}")
            for c in r["concepts"]:
                logger.info(
                    f"      - [{c['category']}] {c['label']} "
                    f"(relevance: {c['relevance_score']})"
                )

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
