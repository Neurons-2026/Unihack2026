"""
Incremental Knowledge Graph Builder — Takes new concepts and an existing
knowledge graph, uses Claude LLM to detect edges among new concepts AND
between new concepts and existing concepts, then merges everything into
a single output graph (old edges + new edges).

Usage (as module):
    from test_graph_building.graph_incremental_llm import merge_new_concepts
    merged_graph = merge_new_concepts(new_concept_files, existing_graph_path, api_key)
"""

import json
import logging
import math
import re
import time
from pathlib import Path

import anthropic
import networkx as nx

logger = logging.getLogger(__name__)

BATCH_SIZE = 30

INCREMENTAL_EDGE_PROMPT = """\
You are an expert AI/ML knowledge graph builder. You are given two groups of \
concepts:

**NEW CONCEPTS** — recently discovered concepts that need to be integrated \
into an existing knowledge graph.

**EXISTING CONCEPTS** — concepts already in the knowledge graph (provided for \
context so you can find connections).

Your task: Identify all meaningful relationships that involve at least one \
NEW concept. This includes:
1. Edges between two NEW concepts.
2. Edges from a NEW concept to an EXISTING concept (or vice versa).

Do NOT create edges between two EXISTING concepts — those already exist in \
the graph.

For each relationship, provide:
1. **source**: The label of the source concept (prerequisite / foundation).
2. **target**: The label of the target concept (depends on / extends / uses source).
3. **relation**: A short phrase. Use one of these when applicable:
   - "depends on" — target requires source as a prerequisite
   - "is a type of" — target is a specialization of source
   - "extends" — target builds upon or improves source
   - "uses" — target employs source as a component or technique
   - "enables" — source makes target possible
   - "competes with" — source and target are alternatives for the same goal
   - "evaluates" — source is used to measure/benchmark target
   - Or use a custom short phrase if none of the above fit.
4. **strength**: A float from 0.0 to 1.0 (1.0 = very direct, 0.3 = minimum).
5. **explanation**: One sentence explaining why this relationship exists.

Rules:
- Only include relationships that are genuinely meaningful and defensible.
- At least one side of every edge MUST be a NEW concept.
- Prefer precision over recall.
- Minimum strength threshold: only include relationships with strength >= 0.3.

Respond ONLY with a valid JSON object:
{
  "edges": [
    {
      "source": "concept A label",
      "target": "concept B label",
      "relation": "depends on",
      "strength": 0.9,
      "explanation": "Why this relationship exists."
    }
  ]
}
"""


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.strip().startswith("```") and not in_block:
                in_block = True
                continue
            elif line.strip() == "```" and in_block:
                break
            elif in_block:
                json_lines.append(line)
        return "\n".join(json_lines)
    return text


def _call_claude(
    client: anthropic.Anthropic,
    prompt: str,
    model: str = "claude-sonnet-4-6",
    max_retries: int = 3,
) -> str:
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model=model,
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
            )
            return _strip_code_fences(message.content[0].text)
        except anthropic.RateLimitError:
            if attempt < max_retries - 1:
                wait = 60 * (attempt + 1)
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{max_retries}). "
                    f"Waiting {wait}s..."
                )
                time.sleep(wait)
            else:
                raise


def load_existing_graph(graph_path: str | Path) -> nx.DiGraph:
    """Load an existing knowledge graph from node-link JSON."""
    with open(graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    G = nx.node_link_graph(data, directed=True, edges="links")
    logger.info(
        f"Loaded existing graph: {G.number_of_nodes()} nodes, "
        f"{G.number_of_edges()} edges"
    )
    return G


def load_new_concepts(concept_files: list[str | Path]) -> list[dict]:
    """Load new concepts from concept JSON files (one per paper)."""
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

    logger.info(f"Loaded {len(nodes)} new concepts from {len(concept_files)} files")
    return nodes


def _format_concept_list(nodes: list[dict], header: str) -> str:
    lines = [f"### {header}\n"]
    for i, node in enumerate(nodes, 1):
        lines.append(f"{i}. **{node['label']}**: {node['description']}")
    return "\n".join(lines)


def _detect_incremental_edges_batch(
    client: anthropic.Anthropic,
    new_nodes: list[dict],
    existing_nodes: list[dict],
    model: str,
) -> list[dict]:
    """
    Single LLM call to detect edges involving new concepts.
    existing_nodes provides context for cross-connections.
    """
    new_text = _format_concept_list(new_nodes, "NEW CONCEPTS")
    existing_text = _format_concept_list(existing_nodes, "EXISTING CONCEPTS")

    prompt = (
        f"{INCREMENTAL_EDGE_PROMPT}\n\n"
        f"--- CONCEPTS ---\n\n{new_text}\n\n{existing_text}"
    )

    response_text = _call_claude(client, prompt, model)
    response_text = re.sub(r",\s*([}\]])", r"\1", response_text)

    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.debug(f"Response was: {response_text[:500]}")
        return []

    new_labels = {node["label"] for node in new_nodes}
    all_labels = new_labels | {node["label"] for node in existing_nodes}

    edges = []
    for edge in parsed.get("edges", []):
        src = edge.get("source", "").strip()
        tgt = edge.get("target", "").strip()
        # Both must be known labels
        if src not in all_labels or tgt not in all_labels:
            logger.warning(f"Skipping edge with unknown label: {src!r} -> {tgt!r}")
            continue
        # At least one must be a new concept
        if src not in new_labels and tgt not in new_labels:
            continue
        if src == tgt:
            continue
        edges.append({
            "source": src,
            "target": tgt,
            "relation": edge.get("relation", "related to"),
            "strength": float(edge.get("strength", 0.5)),
            "explanation": edge.get("explanation", ""),
        })

    logger.info(f"Batch returned {len(edges)} valid new edges")
    return edges


def detect_incremental_edges(
    new_nodes: list[dict],
    existing_nodes: list[dict],
    api_key: str,
    model: str = "claude-sonnet-4-6",
) -> list[dict]:
    """
    Use Claude to detect edges involving new concepts.

    Strategy:
    1. New-to-new edges: process new concepts among themselves.
    2. New-to-existing edges: batch new concepts against chunks of existing
       concepts so the LLM can find cross-connections.
    """
    client = anthropic.Anthropic(api_key=api_key)
    all_edges = []

    # --- Step 1: edges among new concepts ---
    if len(new_nodes) > 1:
        logger.info(f"Step 1: Detecting edges among {len(new_nodes)} new concepts")
        # For new-to-new, pass new concepts as both new and no existing
        edges = _detect_incremental_edges_batch(
            client, new_nodes, [], model
        )
        all_edges.extend(edges)

    # --- Step 2: edges between new and existing concepts ---
    n_existing = len(existing_nodes)
    if n_existing == 0:
        logger.info("No existing concepts — skipping cross-connection step")
    else:
        # Batch existing concepts to keep prompt size manageable
        existing_batch_size = BATCH_SIZE
        n_batches = math.ceil(n_existing / existing_batch_size)
        logger.info(
            f"Step 2: Detecting cross-edges ({len(new_nodes)} new × "
            f"{n_existing} existing in {n_batches} batches)"
        )

        for i in range(0, n_existing, existing_batch_size):
            existing_batch = existing_nodes[i : i + existing_batch_size]
            batch_num = (i // existing_batch_size) + 1
            logger.info(
                f"  Cross-batch {batch_num}/{n_batches} "
                f"({len(existing_batch)} existing concepts)"
            )
            edges = _detect_incremental_edges_batch(
                client, new_nodes, existing_batch, model
            )
            all_edges.extend(edges)

    # Deduplicate
    seen = set()
    unique_edges = []
    for edge in all_edges:
        key = (edge["source"], edge["target"], edge["relation"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(edge)

    logger.info(f"Total unique new edges detected: {len(unique_edges)}")
    return unique_edges


def merge_into_graph(
    existing_graph: nx.DiGraph,
    new_nodes: list[dict],
    new_edges: list[dict],
) -> nx.DiGraph:
    """
    Merge new nodes and edges into a copy of the existing graph.
    Returns the merged graph (does not mutate the original).
    """
    G = existing_graph.copy()

    # Build label -> id mapping across all nodes (existing + new)
    label_to_id = {}
    for node_id, data in G.nodes(data=True):
        label_to_id[data.get("label", "")] = node_id

    # Add new nodes
    added_nodes = 0
    for node in new_nodes:
        if node["id"] not in G:
            G.add_node(node["id"], **node)
            added_nodes += 1
        label_to_id[node["label"]] = node["id"]

    # Add new edges
    added_edges = 0
    for edge in new_edges:
        src_id = label_to_id.get(edge["source"])
        tgt_id = label_to_id.get(edge["target"])
        if src_id and tgt_id:
            G.add_edge(
                src_id,
                tgt_id,
                relation=edge["relation"],
                weight=round(edge["strength"], 4),
                strength=round(edge["strength"], 4),
                similarity=round(edge["strength"], 4),
                explanation=edge["explanation"],
            )
            added_edges += 1

    logger.info(
        f"Merged graph: added {added_nodes} nodes + {added_edges} edges. "
        f"Total: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges"
    )
    return G


def save_graph(G: nx.DiGraph, output_dir: str | Path) -> Path:
    """Save directed graph as node-link JSON."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "knowledge_graph.json"
    graph_data = nx.node_link_data(G, edges="links")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved merged graph: {json_path}")
    return json_path


def print_merge_summary(
    original_graph: nx.DiGraph,
    merged_graph: nx.DiGraph,
    new_nodes: list[dict],
    new_edges: list[dict],
) -> None:
    print(f"\n{'=' * 60}")
    print("Incremental Graph Merge Summary")
    print(f"  Original: {original_graph.number_of_nodes()} nodes, "
          f"{original_graph.number_of_edges()} edges")
    print(f"  New concepts added: {len(new_nodes)}")
    print(f"  New edges added: {len(new_edges)}")
    print(f"  Merged: {merged_graph.number_of_nodes()} nodes, "
          f"{merged_graph.number_of_edges()} edges")

    if new_edges:
        new_labels = {n["label"] for n in new_nodes}

        print(f"\nNew edges (by strength):")
        sorted_edges = sorted(new_edges, key=lambda e: -e["strength"])
        for e in sorted_edges:
            marker_src = " [NEW]" if e["source"] in new_labels else ""
            marker_tgt = " [NEW]" if e["target"] in new_labels else ""
            print(
                f"  [{e['strength']:.2f}] {e['source']}{marker_src}  "
                f"--({e['relation']})--> {e['target']}{marker_tgt}"
            )

        # Relationship type counts for new edges
        relations = {}
        for e in new_edges:
            r = e["relation"]
            relations[r] = relations.get(r, 0) + 1
        print(f"\nNew edge relationship types:")
        for r, count in sorted(relations.items(), key=lambda x: -x[1]):
            print(f"  {r}: {count}")

    print(f"{'=' * 60}\n")
