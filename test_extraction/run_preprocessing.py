"""
Main runner script - Processes all PDFs and GitHub repo links
from resource/test/ and saves cleaned text to resource/processed_test/.

Usage:
    python -m test_extraction.run_preprocessing
    # or
    python test_extraction/run_preprocessing.py
"""

import os
import sys
import logging
from pathlib import Path
from glob import glob

# Ensure project root is on sys.path when run as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from test_extraction.pdf_preprocessor import process_pdf
from test_extraction.github_preprocessor import process_github_link

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Paths
INPUT_DIR = PROJECT_ROOT / "resource" / "test"
OUTPUT_DIR = PROJECT_ROOT / "resource" / "processed_test"


def process_all_pdfs(input_dir: Path, output_dir: Path) -> list[str]:
    """Find and process all PDF files in the input directory."""
    pdf_files = sorted(input_dir.glob("*.pdf"))
    results = []

    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return results

    logger.info(f"Found {len(pdf_files)} PDF file(s) to process")

    for pdf_path in pdf_files:
        output_path = output_dir / f"{pdf_path.stem}.txt"
        try:
            text = process_pdf(str(pdf_path), str(output_path))
            if text:
                results.append(str(output_path))
                logger.info(f"  OK: {pdf_path.name} -> {output_path.name}")
            else:
                logger.error(f"  FAIL: {pdf_path.name} (no text extracted)")
        except Exception as e:
            logger.error(f"  FAIL: {pdf_path.name}: {e}")

    return results


def process_all_github_links(input_dir: Path, output_dir: Path) -> list[str]:
    """Find and process all GitHub repo link files in the input directory."""
    link_files = sorted(input_dir.glob("trendingRepoLink*.txt"))
    results = []

    if not link_files:
        logger.warning(f"No GitHub repo link files found in {input_dir}")
        return results

    logger.info(f"Found {len(link_files)} GitHub repo link file(s) to process")

    # Check for GitHub token in environment (optional, for higher rate limits)
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        logger.info("Using GITHUB_TOKEN for API requests")
    else:
        logger.info(
            "No GITHUB_TOKEN set - using unauthenticated requests "
            "(60 requests/hour limit)"
        )

    for link_file in link_files:
        output_path = output_dir / f"{link_file.stem}.txt"
        try:
            text = process_github_link(str(link_file), str(output_path), github_token)
            if text:
                results.append(str(output_path))
                logger.info(f"  OK: {link_file.name} -> {output_path.name}")
            else:
                logger.error(f"  FAIL: {link_file.name} (no content fetched)")
        except Exception as e:
            logger.error(f"  FAIL: {link_file.name}: {e}")

    return results


def main():
    """Run the full preprocessing pipeline."""
    logger.info("=" * 60)
    logger.info("Starting preprocessing pipeline")
    logger.info(f"  Input directory:  {INPUT_DIR}")
    logger.info(f"  Output directory: {OUTPUT_DIR}")
    logger.info("=" * 60)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []

    # Process PDFs
    logger.info("\n--- Processing PDFs ---")
    pdf_results = process_all_pdfs(INPUT_DIR, OUTPUT_DIR)
    all_results.extend(pdf_results)

    # Process GitHub repo links
    logger.info("\n--- Processing GitHub Repo Links ---")
    github_results = process_all_github_links(INPUT_DIR, OUTPUT_DIR)
    all_results.extend(github_results)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Preprocessing complete!")
    logger.info(f"  Total files processed: {len(all_results)}")
    logger.info(f"  Output directory: {OUTPUT_DIR}")

    if all_results:
        logger.info("  Output files:")
        for result_path in all_results:
            logger.info(f"    - {Path(result_path).name}")
    else:
        logger.warning("  No files were successfully processed.")

    logger.info("=" * 60)

    return all_results


if __name__ == "__main__":
    main()
