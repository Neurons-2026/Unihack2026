"""
Runner script for concept extraction pipeline.
Processes all text files in resource/processed_test/ and outputs
structured concept JSON to resource/processed_test/concepts/.

Each file is processed individually with its own API call.

Usage:
    python -m test_extraction.run_concept_extraction
    python -m test_extraction.run_concept_extraction --model claude-sonnet-4-6
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

from dotenv import load_dotenv

from test_extraction.concept_extractor import (
    extract_concepts_from_file,
    result_to_dict,
)

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PROCESSED_DIR = PROJECT_ROOT / "resource" / "processed_test"
CONCEPTS_OUTPUT_DIR = PROCESSED_DIR / "concepts"


def save_result(result_dict: dict, output_dir: Path) -> None:
    """Save a single extraction result to JSON."""
    output_path = output_dir / f"{Path(result_dict['source_file']).stem}_concepts.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)
    logger.info(f"  Saved: {output_path.name}")


def main():
    parser = argparse.ArgumentParser(description="Extract concepts from processed text")
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        help="Claude model to use (default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Process only this specific file (filename, not full path)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Anthropic API key (or set ANTHROPIC_API_KEY / ANTHTROPIC_API env var)",
    )
    args = parser.parse_args()

    api_key = (
        args.api_key
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ANTHTROPIC_API")
    )
    if not api_key:
        logger.error(
            "No API key provided. Set ANTHROPIC_API_KEY or ANTHTROPIC_API in .env, or use --api-key."
        )
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Concept Extraction Pipeline")
    logger.info(f"  Model:      {args.model}")
    logger.info(f"  Input dir:  {PROCESSED_DIR}")
    logger.info(f"  Output dir: {CONCEPTS_OUTPUT_DIR}")
    logger.info("=" * 60)

    CONCEPTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Single file mode
    if args.file:
        target = PROCESSED_DIR / args.file
        if not target.exists():
            logger.error(f"File not found: {target}")
            sys.exit(1)
        try:
            result = extract_concepts_from_file(str(target), args.model, api_key)
            result_dict = result_to_dict(result)
            save_result(result_dict, CONCEPTS_OUTPUT_DIR)
            logger.info(f"  Concepts: {[c['label'] for c in result_dict['concepts']]}")
        except Exception as e:
            logger.error(f"  FAIL: {target.name}: {e}")
        return

    # Process all text files individually
    all_txt = sorted(f for f in PROCESSED_DIR.glob("*.txt") if f.is_file())

    logger.info(f"\nProcessing {len(all_txt)} file(s) individually\n")

    all_results = []

    for i, txt_file in enumerate(all_txt, 1):
        logger.info(f"[{i}/{len(all_txt)}] {txt_file.name}")
        try:
            result = extract_concepts_from_file(str(txt_file), args.model, api_key)
            result_dict = result_to_dict(result)
            save_result(result_dict, CONCEPTS_OUTPUT_DIR)
            logger.info(f"  Concepts: {[c['label'] for c in result_dict['concepts']]}")
            all_results.append(result_dict)
        except Exception as e:
            logger.error(f"  FAIL: {txt_file.name}: {e}")

    # Write combined summary
    if all_results:
        summary_path = CONCEPTS_OUTPUT_DIR / "all_concepts_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("Extraction complete!")
    logger.info(f"  Files processed: {len(all_results)} / {len(all_txt)}")

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
