"""
Runner script for description-enriched knowledge graph building.

Uses concept files from backend/data/concepts/ (trending papers 1 & 2)
and embeds label+description for edge similarity.

Usage:
    python -m test_graph_building.run_graph_description
    python -m test_graph_building.run_graph_description --threshold 0.5
"""

import argparse
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from test_graph_building.graph_builder_description import (
    load_concepts_from_files,
    embed_label_and_description,
    build_graph,
    save_graph,
    print_graph_summary,
)

load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

CONCEPTS_DIR = PROJECT_ROOT / "backend" / "data" / "concepts"
OUTPUT_DIR = PROJECT_ROOT / "test_graph_building" / "output_description"


def main():
    parser = argparse.ArgumentParser(
        description="Build knowledge graph using label+description embeddings"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.4,
        help="Cosine similarity threshold for edges (default: 0.4)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory (default: test_graph_building/output_description)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="OpenAI API key (or set OPENAI_API / OPENAI_API_KEY env var)",
    )
    args = parser.parse_args()

    api_key = (
        args.api_key
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("OPENAI_API")
    )
    if not api_key:
        logger.error("No OpenAI API key. Set OPENAI_API or OPENAI_API_KEY in .env, or use --api-key.")
        sys.exit(1)

    output_dir = Path(args.output) if args.output else OUTPUT_DIR

    # Collect concept files from backend/data/concepts/
    concept_files = sorted(CONCEPTS_DIR.glob("*_concepts.json"))
    if not concept_files:
        logger.error(f"No concept files found in {CONCEPTS_DIR}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Knowledge Graph Builder (label+description embeddings)")
    logger.info(f"  Input files: {[f.name for f in concept_files]}")
    logger.info(f"  Output:      {output_dir}")
    logger.info(f"  Threshold:   {args.threshold}")
    logger.info("=" * 60)

    # Load concepts
    nodes = load_concepts_from_files(concept_files)

    # Embed label + description
    embeddings = embed_label_and_description(nodes, api_key)

    # Build graph
    G = build_graph(nodes, embeddings, similarity_threshold=args.threshold)

    # Save
    save_graph(G, output_dir)

    # Print summary
    print_graph_summary(G)

    logger.info("Done!")


if __name__ == "__main__":
    main()
