"""
Runner script for building a knowledge graph from general_ai_concepts.json.

Usage:
    python -m test_graph_building.run_graph_general
    python -m test_graph_building.run_graph_general --threshold 0.5
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

from test_graph_building.graph_builder_description import (
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

CONCEPTS_FILE = Path(__file__).resolve().parent / "general_ai_concepts.json"
OUTPUT_DIR = Path(__file__).resolve().parent / "output_general"


def load_general_concepts(path: Path) -> list[dict]:
    """Load concepts from general_ai_concepts.json (array-of-sources format)."""
    with open(path, "r", encoding="utf-8") as f:
        sources = json.load(f)

    nodes = []
    for source in sources:
        for concept in source["concepts"]:
            nodes.append({
                "id": f"{source['source_file']}::{concept['label']}",
                "label": concept["label"],
                "description": concept["description"],
                "why_innovative": concept["why_innovative"],
                "impact_on_applications": concept.get("impact_on_applications", ""),
                "category": concept["category"],
                "relevance_score": concept["relevance_score"],
                "source_file": source["source_file"],
                "source_title": source["source_title"],
            })

    logger.info(f"Loaded {len(nodes)} concepts from {path.name}")
    return nodes


def main():
    parser = argparse.ArgumentParser(
        description="Build knowledge graph from general AI concepts using label+description embeddings"
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
        help="Output directory (default: test_graph_building/output_general)",
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

    logger.info("=" * 60)
    logger.info("Knowledge Graph Builder (general AI concepts, label+description)")
    logger.info(f"  Input:     {CONCEPTS_FILE.name}")
    logger.info(f"  Output:    {output_dir}")
    logger.info(f"  Threshold: {args.threshold}")
    logger.info("=" * 60)

    nodes = load_general_concepts(CONCEPTS_FILE)
    embeddings = embed_label_and_description(nodes, api_key)
    G = build_graph(nodes, embeddings, similarity_threshold=args.threshold)
    save_graph(G, output_dir)
    print_graph_summary(G)

    logger.info("Done!")


if __name__ == "__main__":
    main()
