"""
Knowledge Graph Builder (LLM-based) — Uses Claude to identify semantic
dependency and relationship edges between concepts, producing a concept map
with typed, directed edges rather than embedding-similarity edges.

This captures richer relationships like "depends on", "is a type of",
"extends", "uses", etc.
"""

import json
import logging
import math
import os
import time
from pathlib import Path

import anthropic
import networkx as nx

logger = logging.getLogger(__name__)

# Max concepts per LLM call — keeps prompt manageable and output reliable
BATCH_SIZE = 30

EDGE_DETECTION_PROMPT = """\
You are an expert AI/ML knowledge graph builder. Given a list of concepts \
(each with a label and description), identify all meaningful relationships \
between them.

For each relationship, provide:
1. **source**: The label of the concept that is the prerequisite / foundation / \
input (the concept that must exist first or that the other concept builds upon).
2. **target**: The label of the concept that depends on / extends / uses the source.
3. **relation**: A short phrase describing the relationship. Use one of these \
types when applicable:
   - "depends on" — target requires source as a prerequisite
   - "is a type of" — target is a specialization of source
   - "extends" — target builds upon or improves source
   - "uses" — target employs source as a component or technique
   - "enables" — source makes target possible
   - "competes with" — source and target are alternatives for the same goal
   - "evaluates" — source is used to measure/benchmark target
   - Or use a custom short phrase if none of the above fit.
4. **strength**: A float from 0.0 to 1.0 indicating how strong/direct the \
relationship is (1.0 = very direct dependency, 0.5 = moderate, 0.2 = loose).
5. **explanation**: One sentence explaining why this relationship exists.

Rules:
- Only include relationships that are genuinely meaningful and defensible.
- Do NOT create edges between every pair — focus on real dependencies and \
relationships that a domain expert would agree with.
- A concept can have multiple relationships (both incoming and outgoing).
- Prefer precision over recall — it's better to miss a weak relationship than \
to include a spurious one.
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


def _get_api_key(api_key: str | None = None) -> str:
    key = (
        api_key
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ANTHTROPIC_API")
    )
    if not key:
        raise ValueError(
            "No Anthropic API key found. "
            "Set ANTHROPIC_API_KEY or ANTHTROPIC_API env var."
        )
    return key


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


def _format_concepts_for_prompt(nodes: list[dict]) -> str:
    lines = []
    for i, node in enumerate(nodes, 1):
        lines.append(
            f"{i}. **{node['label']}**: {node['description']}"
        )
    return "\n".join(lines)


def detect_edges_with_llm(
    nodes: list[dict],
    api_key: str,
    model: str = "claude-sonnet-4-6",
) -> list[dict]:
    """
    Use Claude to identify dependency/relationship edges between concepts.

    For large concept lists, splits into batches and also does a cross-batch
    pass to catch inter-batch relationships.
    """
    key = _get_api_key(api_key)
    client = anthropic.Anthropic(api_key=key)

    n = len(nodes)
    all_edges = []

    if n <= BATCH_SIZE:
        # Small enough to process in one call
        logger.info(f"Detecting edges for {n} concepts in a single LLM call")
        edges = _detect_edges_batch(client, nodes, model)
        all_edges.extend(edges)
    else:
        # Split into batches
        n_batches = math.ceil(n / BATCH_SIZE)
        logger.info(
            f"Splitting {n} concepts into {n_batches} batches of ~{BATCH_SIZE}"
        )

        batches = []
        for i in range(0, n, BATCH_SIZE):
            batches.append(nodes[i : i + BATCH_SIZE])

        # Process each batch
        for i, batch in enumerate(batches):
            logger.info(
                f"Processing batch {i + 1}/{n_batches} "
                f"({len(batch)} concepts)"
            )
            edges = _detect_edges_batch(client, batch, model)
            all_edges.extend(edges)

        # Cross-batch pass: for each pair of batches, ask about
        # inter-batch relationships
        for i in range(len(batches)):
            for j in range(i + 1, len(batches)):
                logger.info(
                    f"Cross-batch pass: batch {i + 1} x batch {j + 1}"
                )
                combined = batches[i] + batches[j]
                edges = _detect_edges_batch(client, combined, model)
                # Only keep edges that cross batches
                labels_i = {node["label"] for node in batches[i]}
                labels_j = {node["label"] for node in batches[j]}
                cross_edges = [
                    e for e in edges
                    if (e["source"] in labels_i and e["target"] in labels_j)
                    or (e["source"] in labels_j and e["target"] in labels_i)
                ]
                all_edges.extend(cross_edges)

    # Deduplicate edges
    seen = set()
    unique_edges = []
    for edge in all_edges:
        key_tuple = (edge["source"], edge["target"], edge["relation"])
        if key_tuple not in seen:
            seen.add(key_tuple)
            unique_edges.append(edge)

    logger.info(f"Total unique edges detected: {len(unique_edges)}")
    return unique_edges


def _detect_edges_batch(
    client: anthropic.Anthropic,
    nodes: list[dict],
    model: str,
) -> list[dict]:
    """Detect edges for a single batch of concepts."""
    concepts_text = _format_concepts_for_prompt(nodes)
    prompt = (
        f"{EDGE_DETECTION_PROMPT}\n\n"
        f"--- CONCEPTS ---\n\n{concepts_text}"
    )

    response_text = _call_claude(client, prompt, model)

    import re
    response_text = re.sub(r",\s*([}\]])", r"\1", response_text)

    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.debug(f"Response was: {response_text[:500]}")
        return []

    valid_labels = {node["label"] for node in nodes}
    edges = []
    for edge in parsed.get("edges", []):
        src = edge.get("source", "").strip()
        tgt = edge.get("target", "").strip()
        if src not in valid_labels or tgt not in valid_labels:
            logger.warning(
                f"Skipping edge with unknown label: {src!r} -> {tgt!r}"
            )
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

    logger.info(f"Batch returned {len(edges)} valid edges")
    return edges


def build_graph(nodes: list[dict], edges: list[dict]) -> nx.DiGraph:
    """
    Build a directed knowledge graph from concepts and LLM-detected edges.
    """
    G = nx.DiGraph()

    # Build label -> id mapping
    label_to_id = {}
    for node in nodes:
        G.add_node(node["id"], **node)
        label_to_id[node["label"]] = node["id"]

    edge_count = 0
    for edge in edges:
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
            edge_count += 1

    logger.info(
        f"Built directed graph: {G.number_of_nodes()} nodes, "
        f"{edge_count} edges"
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
    logger.info(f"Saved graph JSON: {json_path}")
    return json_path


def print_graph_summary(G: nx.DiGraph) -> None:
    print(f"\n{'=' * 60}")
    print(f"Knowledge Graph Summary (LLM-detected relationships)")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    print(f"  Graph type: Directed")

    if G.number_of_edges() > 0:
        strengths = [d["strength"] for _, _, d in G.edges(data=True)]
        import numpy as np
        print(f"  Strength range: {min(strengths):.2f} - {max(strengths):.2f}")
        print(f"  Mean strength:  {np.mean(strengths):.2f}")

        # Count relation types
        relations = {}
        for _, _, d in G.edges(data=True):
            r = d["relation"]
            relations[r] = relations.get(r, 0) + 1
        print(f"\nRelationship types:")
        for r, count in sorted(relations.items(), key=lambda x: -x[1]):
            print(f"  {r}: {count}")

    print(f"\nEdges (by strength):")
    for u, v, d in sorted(G.edges(data=True), key=lambda x: -x[2]["strength"]):
        label_u = G.nodes[u]["label"]
        label_v = G.nodes[v]["label"]
        print(
            f"  [{d['strength']:.2f}] {label_u}  --({d['relation']})--> "
            f"{label_v}"
        )

    # Hub nodes (highest out-degree)
    print(f"\nTop prerequisite nodes (highest out-degree):")
    out_sorted = sorted(G.nodes(), key=lambda n: G.out_degree(n), reverse=True)
    for node_id in out_sorted[:10]:
        label = G.nodes[node_id]["label"]
        print(f"  {label}: {G.out_degree(node_id)} outgoing edges")

    isolated = list(nx.isolates(G))
    if isolated:
        print(f"\nIsolated nodes (no edges):")
        for node_id in isolated:
            print(f"  - {G.nodes[node_id]['label']}")

    print(f"{'=' * 60}\n")
