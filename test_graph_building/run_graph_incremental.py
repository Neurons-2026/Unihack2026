"""
Runner script for incrementally adding new concepts to an existing knowledge
graph using Claude LLM to detect relationship edges.

Usage:
    python -m test_graph_building.run_graph_incremental
    python -m test_graph_building.run_graph_incremental --new-concepts path1.json path2.json
    python -m test_graph_building.run_graph_incremental --graph path/to/knowledge_graph.json
"""

import argparse
import logging
import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from test_graph_building.graph_incremental_llm import (
    load_existing_graph,
    load_new_concepts,
    detect_incremental_edges,
    merge_into_graph,
    save_graph,
    print_merge_summary,
)

load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Defaults
DEFAULT_GRAPH = Path(__file__).resolve().parent / "output_llm" / "knowledge_graph.json"
DEFAULT_NEW_CONCEPTS = [
    Path(__file__).resolve().parent.parent
    / "resource" / "processed_test" / "concepts" / "trendingPaper1_concepts.json",
    Path(__file__).resolve().parent.parent
    / "resource" / "processed_test" / "concepts" / "trendingPaper2_concepts.json",
]
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "output_incremental"


def main():
    parser = argparse.ArgumentParser(
        description="Incrementally add new concepts to an existing knowledge graph"
    )
    parser.add_argument(
        "--graph",
        default=None,
        help="Path to existing knowledge_graph.json (default: output_llm/knowledge_graph.json)",
    )
    parser.add_argument(
        "--new-concepts",
        nargs="+",
        default=None,
        help="Paths to new concept JSON files (default: trendingPaper1 + trendingPaper2)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory (default: test_graph_building/output_incremental)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        help="Claude model to use (default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
    )
    args = parser.parse_args()

    api_key = (
        args.api_key
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ANTHTROPIC_API")
    )
    if not api_key:
        logger.error("No Anthropic API key. Set ANTHROPIC_API_KEY in .env, or use --api-key.")
        sys.exit(1)

    graph_path = Path(args.graph) if args.graph else DEFAULT_GRAPH
    new_concept_paths = (
        [Path(p) for p in args.new_concepts] if args.new_concepts else DEFAULT_NEW_CONCEPTS
    )
    output_dir = Path(args.output) if args.output else DEFAULT_OUTPUT

    logger.info("=" * 60)
    logger.info("Incremental Knowledge Graph Builder")
    logger.info(f"  Existing graph: {graph_path}")
    logger.info(f"  New concepts:   {[p.name for p in new_concept_paths]}")
    logger.info(f"  Output:         {output_dir}")
    logger.info(f"  Model:          {args.model}")
    logger.info("=" * 60)

    # Load existing graph
    existing_graph = load_existing_graph(graph_path)

    # Extract existing node info for the LLM context
    existing_nodes = []
    for node_id, data in existing_graph.nodes(data=True):
        existing_nodes.append({
            "id": node_id,
            "label": data.get("label", ""),
            "description": data.get("description", ""),
        })

    # Load new concepts
    new_nodes = load_new_concepts(new_concept_paths)

    # Detect new edges using Claude
    new_edges = detect_incremental_edges(
        new_nodes, existing_nodes, api_key, model=args.model
    )

    # Merge into graph
    merged_graph = merge_into_graph(existing_graph, new_nodes, new_edges)

    # Save
    save_graph(merged_graph, output_dir)
    print_merge_summary(existing_graph, merged_graph, new_nodes, new_edges)

    # Generate visualization
    graph_json_path = output_dir / "knowledge_graph.json"
    try:
        subprocess.run(
            [
                sys.executable, "-m", "test_graph_building.generate_viz",
                str(graph_json_path),
                "--title", "AI Concepts — Incremental LLM Graph",
            ],
            check=True,
        )
        logger.info(f"Generated visualization: {output_dir / 'visualize.html'}")
    except subprocess.CalledProcessError:
        logger.warning("Visualization generation failed, skipping")

    logger.info("Done!")


if __name__ == "__main__":
    main()
