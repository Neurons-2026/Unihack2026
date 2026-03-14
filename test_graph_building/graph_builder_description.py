"""
Knowledge Graph Builder (Description-Enriched) — Builds a concept graph where
edges are based on cosine similarity of combined label+description embeddings
(OpenAI text-embedding-3-large), rather than label-only embeddings.

This allows the graph to capture semantic similarity between concepts that have
different names but describe related ideas.
"""

import json
import logging
import os
from pathlib import Path

import numpy as np
import networkx as nx
from openai import OpenAI

logger = logging.getLogger(__name__)


def _cosine_similarity_matrix(embeddings: list[list[float]]) -> np.ndarray:
    mat = np.array(embeddings)
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    normed = mat / norms
    return normed @ normed.T


def load_concepts_from_files(concept_files: list[str | Path]) -> list[dict]:
    """Load concepts from individual concept JSON files (one per paper)."""
    nodes = []
    for path in concept_files:
        with open(path, "r", encoding="utf-8") as f:
            source = json.load(f)

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

    logger.info(f"Loaded {len(nodes)} concepts from {len(concept_files)} files")
    return nodes


def embed_label_and_description(nodes: list[dict], api_key: str) -> list[list[float]]:
    """Embed combined 'label: description' using OpenAI text-embedding-3-large."""
    client = OpenAI(api_key=api_key)
    texts = [f"{node['label']}: {node['description']}" for node in nodes]

    logger.info(f"Embedding {len(texts)} label+description texts with text-embedding-3-large")
    response = client.embeddings.create(input=texts, model="text-embedding-3-large")

    embeddings = [item.embedding for item in response.data]
    logger.info(f"Got {len(embeddings)} embeddings, dim={len(embeddings[0])}")
    return embeddings


def build_graph(
    nodes: list[dict],
    embeddings: list[list[float]],
    similarity_threshold: float = 0.4,
) -> nx.Graph:
    """
    Build knowledge graph.
    - Nodes carry full concept metadata.
    - Edges connect concepts with cosine similarity >= threshold.
    """
    G = nx.Graph()

    for node in nodes:
        G.add_node(node["id"], **node)

    sim_matrix = _cosine_similarity_matrix(embeddings)
    n = len(nodes)
    edge_count = 0

    for i in range(n):
        for j in range(i + 1, n):
            sim = float(sim_matrix[i, j])
            if sim >= similarity_threshold:
                G.add_edge(
                    nodes[i]["id"],
                    nodes[j]["id"],
                    weight=round(sim, 4),
                    similarity=round(sim, 4),
                )
                edge_count += 1

    logger.info(
        f"Built graph: {G.number_of_nodes()} nodes, {edge_count} edges "
        f"(threshold={similarity_threshold})"
    )
    return G


def save_graph(G: nx.Graph, output_dir: str | Path) -> Path:
    """Save graph as node-link JSON."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "knowledge_graph.json"
    graph_data = nx.node_link_data(G, edges="links")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved graph JSON: {json_path}")
    return json_path


def print_graph_summary(G: nx.Graph) -> None:
    print(f"\n{'=' * 60}")
    print(f"Knowledge Graph Summary (label+description embeddings)")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")

    if G.number_of_edges() > 0:
        weights = [d["weight"] for _, _, d in G.edges(data=True)]
        print(f"  Similarity range: {min(weights):.4f} - {max(weights):.4f}")
        print(f"  Mean similarity:  {np.mean(weights):.4f}")

    print(f"\nEdges (by similarity):")
    for u, v, d in sorted(G.edges(data=True), key=lambda x: -x[2]["weight"]):
        label_u = G.nodes[u]["label"]
        label_v = G.nodes[v]["label"]
        print(f"  [{d['weight']:.4f}] {label_u}  <-->  {label_v}")

    isolated = list(nx.isolates(G))
    if isolated:
        print(f"\nIsolated nodes (no edges above threshold):")
        for node_id in isolated:
            print(f"  - {G.nodes[node_id]['label']}")

    print(f"{'=' * 60}\n")
