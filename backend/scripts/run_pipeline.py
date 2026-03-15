"""
Run the full ingestion pipeline: Scrape → Preprocess → Cards → Concepts → DB.

Usage:
    cd backend
    python -m scripts.run_pipeline
    python -m scripts.run_pipeline --sources github huggingface
    python -m scripts.run_pipeline --no-cards --no-concepts
    python -m scripts.run_pipeline --no-db --dry-run
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure backend/ is on sys.path so services.* imports work
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")

from services.pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Run the full ingestion pipeline: Scrape → Preprocess → Cards → Concepts → DB"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["github", "huggingface", "anthropic", "openai"],
        default=None,
        help="Sources to scrape (default: all)",
    )
    parser.add_argument(
        "--no-cards",
        action="store_true",
        help="Skip card generation (Claude API call)",
    )
    parser.add_argument(
        "--no-concepts",
        action="store_true",
        help="Skip concept extraction from PDFs",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Skip storing to Supabase (still saves locally)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        help="Claude model for concept extraction (default: claude-sonnet-4-6)",
    )
    args = parser.parse_args()

    summary = run_pipeline(
        sources=args.sources,
        generate_cards_flag=not args.no_cards,
        extract_concepts_flag=not args.no_concepts,
        store_to_db=not args.no_db,
        model=args.model,
    )

    print(f"\nPipeline Summary:")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
