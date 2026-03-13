"""
Runner script for concept extraction pipeline.
Processes all text files in resource/processed_test/ and outputs
structured concept JSON to resource/processed_test/concepts/.

Batches GitHub repo files into a single request to minimize API calls.
Total: 4 paper requests + 1 batched repo request = 5 API calls.

Usage:
    python -m test_extraction.run_concept_extraction
    python -m test_extraction.run_concept_extraction --model gemini-2.5-flash-preview-05-20
    python -m test_extraction.run_concept_extraction --file trendingPaper1.txt
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from test_extraction.concept_extractor import (
    extract_concepts_from_file,
    extract_concepts_batch,
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

# Delay between API calls to avoid rate limits (seconds)
REQUEST_DELAY = 5


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
        default="gemini-2.5-flash-preview-05-20",
        help="Gemini model to use (default: gemini-2.5-flash-preview-05-20)",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Process only this specific file (filename, not full path)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Google AI API key (or set GEMINI_API_KEY / GOOGLE_API env var)",
    )
    args = parser.parse_args()

    api_key = (
        args.api_key
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API")
    )
    if not api_key:
        logger.error(
            "No API key provided. Set GEMINI_API_KEY or GOOGLE_API in .env, or use --api-key."
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

    # Full batch mode: separate papers and repo links
    all_txt = sorted(f for f in PROCESSED_DIR.glob("*.txt") if f.is_file())
    paper_files = [f for f in all_txt if f.name.startswith("trendingPaper")]
    repo_files = [f for f in all_txt if f.name.startswith("trendingRepoLink")]

    total_requests = len(paper_files) + (1 if repo_files else 0)
    logger.info(
        f"\nPlan: {len(paper_files)} paper(s) individually + "
        f"{len(repo_files)} repo(s) batched = {total_requests} API call(s)\n"
    )

    all_results = []
    request_count = 0

    # Process each paper individually
    for paper_file in paper_files:
        if request_count > 0:
            logger.info(f"  Waiting {REQUEST_DELAY}s between requests...")
            time.sleep(REQUEST_DELAY)

        logger.info(f"[{request_count + 1}/{total_requests}] {paper_file.name}")
        try:
            result = extract_concepts_from_file(str(paper_file), args.model, api_key)
            result_dict = result_to_dict(result)
            save_result(result_dict, CONCEPTS_OUTPUT_DIR)
            logger.info(f"  Concepts: {[c['label'] for c in result_dict['concepts']]}")
            all_results.append(result_dict)
        except Exception as e:
            logger.error(f"  FAIL: {paper_file.name}: {e}")
        request_count += 1

    # Batch all repo links into a single request
    if repo_files:
        if request_count > 0:
            logger.info(f"  Waiting {REQUEST_DELAY}s between requests...")
            time.sleep(REQUEST_DELAY)

        logger.info(
            f"[{request_count + 1}/{total_requests}] "
            f"Batch: {[f.name for f in repo_files]}"
        )
        try:
            file_texts = []
            for rf in repo_files:
                with open(rf, "r", encoding="utf-8") as f:
                    file_texts.append((rf.name, f.read()))

            batch_results = extract_concepts_batch(file_texts, args.model, api_key)
            for result in batch_results:
                result_dict = result_to_dict(result)
                save_result(result_dict, CONCEPTS_OUTPUT_DIR)
                logger.info(
                    f"  Concepts ({result.source_file}): "
                    f"{[c['label'] for c in result_dict['concepts']]}"
                )
                all_results.append(result_dict)
        except Exception as e:
            logger.error(f"  FAIL (batch): {e}")
        request_count += 1

    # Write combined summary
    if all_results:
        summary_path = CONCEPTS_OUTPUT_DIR / "all_concepts_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("Extraction complete!")
    logger.info(f"  API calls made: {request_count}")
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
