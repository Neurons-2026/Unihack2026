"""
Runner script for concept extraction from scraped PDFs.

Usage:
    python -m backend.scripts.extract_concepts
    python -m backend.scripts.extract_concepts --model claude-sonnet-4-6
    python -m backend.scripts.extract_concepts --file 2603.12180.pdf
    python -m backend.scripts.extract_concepts --no-skip
"""

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    from backend.services.concept_extraction import (
        process_pdf,
        process_all_pdfs,
        save_result,
        PDF_DIR,
        CONCEPTS_DIR,
    )

    parser = argparse.ArgumentParser(
        description="Extract concepts from scraped HuggingFace PDFs"
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Process a single PDF filename (e.g., 2603.12180.pdf)",
    )
    parser.add_argument(
        "--pdf-dir",
        default=None,
        help=f"PDF input directory (default: {PDF_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=f"Concepts output directory (default: {CONCEPTS_DIR})",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        help="Claude model to use (default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Anthropic API key (or set ANTHROPIC_API_KEY / ANTHTROPIC_API env var)",
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Re-process PDFs even if concepts already exist",
    )
    args = parser.parse_args()

    pdf_dir = Path(args.pdf_dir) if args.pdf_dir else PDF_DIR
    output_dir = Path(args.output_dir) if args.output_dir else CONCEPTS_DIR

    logger.info("=" * 60)
    logger.info("Concept Extraction Service")
    logger.info(f"  PDF dir:    {pdf_dir}")
    logger.info(f"  Output dir: {output_dir}")
    logger.info(f"  Model:      {args.model}")
    logger.info("=" * 60)

    if args.file:
        pdf_path = pdf_dir / args.file
        if not pdf_path.exists():
            logger.error(f"PDF not found: {pdf_path}")
            sys.exit(1)

        result = process_pdf(pdf_path, model=args.model, api_key=args.api_key)
        save_result(result, output_dir)

        print(f"\nExtracted {len(result.concepts)} concepts from {args.file}:")
        for c in result.concepts:
            print(f"  [{c.relevance_score:.2f}] {c.label} ({c.category})")
    else:
        results = process_all_pdfs(
            pdf_dir=pdf_dir,
            output_dir=output_dir,
            model=args.model,
            api_key=args.api_key,
            skip_existing=not args.no_skip,
        )

        print(f"\n{'=' * 60}")
        print(f"Concept Extraction Summary")
        print(f"  PDFs processed: {len(results)}")
        total_concepts = sum(len(r.concepts) for r in results)
        print(f"  Total concepts: {total_concepts}")
        for r in results:
            print(f"\n  {r.source_file} -> {r.source_title}")
            for c in r.concepts:
                print(f"    [{c.relevance_score:.2f}] {c.label} ({c.category})")
        print(f"{'=' * 60}")

    logger.info("Done!")


if __name__ == "__main__":
    main()
