import hashlib
import json
import logging
import math
import os
import re
import time
from typing import Any, List

import anthropic

from models.schemas import GraphEdge, GraphNode

logger = logging.getLogger(__name__)

BATCH_SIZE = 30

EDGE_DETECTION_PROMPT = """\
You are an expert AI/ML knowledge graph builder. Given a list of concepts \
(each with a label and description), identify all meaningful relationships \
between them.

For each relationship, provide:
1. source: The label of the concept that is the prerequisite/foundation/input.
2. target: The label of the concept that depends on/extends/uses the source.
3. relation: A short phrase, preferably one of:
   - depends on
   - is a type of
   - extends
   - uses
   - enables
   - competes with
   - evaluates
4. strength: A float from 0.0 to 1.0.
5. explanation: One sentence explaining the relationship.

Rules:
- Include only meaningful and defensible relationships.
- Do not connect every pair.
- Prefer precision over recall.
- Include only relationships with strength >= 0.3.

Respond ONLY with valid JSON:
{
  "edges": [
    {
      "source": "concept A",
      "target": "concept B",
      "relation": "depends on",
      "strength": 0.9,
      "explanation": "Why this relationship exists."
    }
  ]
}
"""

INCREMENTAL_EDGE_PROMPT = """\
You are an expert AI/ML knowledge graph builder. You are given two groups:

NEW CONCEPTS: concepts to integrate.
EXISTING CONCEPTS: concepts already in the graph.

Identify meaningful relationships where at least one side is a NEW concept.
Include:
1. NEW -> NEW edges.
2. NEW <-> EXISTING edges.

Do NOT include EXISTING <-> EXISTING edges.

For each relationship, provide source, target, relation, strength, explanation.
Use relation types where possible:
depends on, is a type of, extends, uses, enables, competes with, evaluates.

Rules:
- Relationships must be meaningful and defensible.
- At least one side must be a NEW concept.
- Prefer precision over recall.
- Include only relationships with strength >= 0.3.

Respond ONLY with valid JSON:
{
  "edges": [
    {
      "source": "concept A",
      "target": "concept B",
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
            if line.strip() == "```" and in_block:
                break
            if in_block:
                json_lines.append(line)
        return "\n".join(json_lines)
    return text


def _call_claude(
    client: anthropic.Anthropic,
    prompt: str,
    model: str,
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
                    "Rate limited (attempt %s/%s). Waiting %ss...",
                    attempt + 1,
                    max_retries,
                    wait,
                )
                time.sleep(wait)
            else:
                raise


def _normalize_concept_sources(concept_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for source in concept_sources:
        source_file = str(source.get("source_file", "unknown")).strip() or "unknown"
        source_title = str(source.get("source_title", source_file)).strip() or source_file
        for concept in source.get("concepts", []):
            label = str(concept.get("label", "")).strip()
            if not label:
                continue
            nodes.append(
                {
                    "id": f"{source_file}::{label}",
                    "label": label,
                    "description": str(concept.get("description", "")).strip(),
                    "why_innovative": str(concept.get("why_innovative", "")).strip(),
                    "impact_on_applications": str(
                        concept.get("impact_on_applications", "")
                    ).strip(),
                    "category": str(concept.get("category", "")).strip(),
                    "relevance_score": float(concept.get("relevance_score", 0.0)),
                    "source_file": source_file,
                    "source_title": source_title,
                }
            )
    return nodes


def _format_concepts_for_prompt(nodes: list[dict[str, Any]]) -> str:
    lines = []
    for i, node in enumerate(nodes, 1):
        lines.append(f"{i}. **{node['label']}**: {node['description']}")
    return "\n".join(lines)


def _detect_edges_batch(
    client: anthropic.Anthropic,
    nodes: list[dict[str, Any]],
    model: str,
) -> list[dict[str, Any]]:
    prompt = (
        f"{EDGE_DETECTION_PROMPT}\n\n"
        f"--- CONCEPTS ---\n\n{_format_concepts_for_prompt(nodes)}"
    )
    response_text = _call_claude(client, prompt, model)
    response_text = re.sub(r",\s*([}\]])", r"\1", response_text)

    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse LLM response as JSON: %s", exc)
        logger.debug("Response was: %s", response_text[:500])
        return []

    valid_labels = {node["label"] for node in nodes}
    edges = []
    for edge in parsed.get("edges", []):
        src = str(edge.get("source", "")).strip()
        tgt = str(edge.get("target", "")).strip()
        if src not in valid_labels or tgt not in valid_labels or src == tgt:
            continue
        edges.append(
            {
                "source": src,
                "target": tgt,
                "relation": str(edge.get("relation", "related to")).strip() or "related to",
                "strength": float(edge.get("strength", 0.5)),
                "explanation": str(edge.get("explanation", "")).strip(),
            }
        )
    return edges


def _detect_edges_with_llm(
    nodes: list[dict[str, Any]],
    api_key: str,
    model: str,
) -> list[dict[str, Any]]:
    client = anthropic.Anthropic(api_key=api_key)
    all_edges: list[dict[str, Any]] = []

    if len(nodes) <= BATCH_SIZE:
        all_edges.extend(_detect_edges_batch(client, nodes, model))
    else:
        batches = [nodes[i : i + BATCH_SIZE] for i in range(0, len(nodes), BATCH_SIZE)]
        for batch in batches:
            all_edges.extend(_detect_edges_batch(client, batch, model))

        for i in range(len(batches)):
            for j in range(i + 1, len(batches)):
                combined = batches[i] + batches[j]
                edges = _detect_edges_batch(client, combined, model)
                labels_i = {node["label"] for node in batches[i]}
                labels_j = {node["label"] for node in batches[j]}
                all_edges.extend(
                    e
                    for e in edges
                    if (e["source"] in labels_i and e["target"] in labels_j)
                    or (e["source"] in labels_j and e["target"] in labels_i)
                )

    seen = set()
    deduped = []
    for edge in all_edges:
        key = (edge["source"], edge["target"], edge["relation"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(edge)
    return deduped


def _format_concept_list(nodes: list[dict[str, Any]], header: str) -> str:
    lines = [f"### {header}\n"]
    for i, node in enumerate(nodes, 1):
        lines.append(f"{i}. **{node['label']}**: {node['description']}")
    return "\n".join(lines)


def _detect_incremental_edges_batch(
    client: anthropic.Anthropic,
    new_nodes: list[dict[str, Any]],
    existing_nodes: list[dict[str, Any]],
    model: str,
) -> list[dict[str, Any]]:
    prompt = (
        f"{INCREMENTAL_EDGE_PROMPT}\n\n"
        f"--- CONCEPTS ---\n\n"
        f"{_format_concept_list(new_nodes, 'NEW CONCEPTS')}\n\n"
        f"{_format_concept_list(existing_nodes, 'EXISTING CONCEPTS')}"
    )
    response_text = _call_claude(client, prompt, model)
    response_text = re.sub(r",\s*([}\]])", r"\1", response_text)

    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse incremental LLM response as JSON: %s", exc)
        logger.debug("Response was: %s", response_text[:500])
        return []

    new_labels = {node["label"] for node in new_nodes}
    all_labels = new_labels | {node["label"] for node in existing_nodes}

    edges = []
    for edge in parsed.get("edges", []):
        src = str(edge.get("source", "")).strip()
        tgt = str(edge.get("target", "")).strip()
        if src not in all_labels or tgt not in all_labels:
            continue
        if src not in new_labels and tgt not in new_labels:
            continue
        if src == tgt:
            continue
        edges.append(
            {
                "source": src,
                "target": tgt,
                "relation": str(edge.get("relation", "related to")).strip() or "related to",
                "strength": float(edge.get("strength", 0.5)),
                "explanation": str(edge.get("explanation", "")).strip(),
            }
        )
    return edges


def _detect_incremental_edges_with_llm(
    new_nodes: list[dict[str, Any]],
    existing_nodes: list[dict[str, Any]],
    api_key: str,
    model: str,
) -> list[dict[str, Any]]:
    client = anthropic.Anthropic(api_key=api_key)
    all_edges: list[dict[str, Any]] = []

    if len(new_nodes) > 1:
        all_edges.extend(_detect_incremental_edges_batch(client, new_nodes, [], model))

    if existing_nodes:
        n_batches = math.ceil(len(existing_nodes) / BATCH_SIZE)
        for i in range(n_batches):
            start = i * BATCH_SIZE
            end = start + BATCH_SIZE
            batch = existing_nodes[start:end]
            all_edges.extend(
                _detect_incremental_edges_batch(client, new_nodes, batch, model)
            )

    seen = set()
    deduped = []
    for edge in all_edges:
        key = (edge["source"], edge["target"], edge["relation"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(edge)
    return deduped


def _edge_id(source_node_id: str, target_node_id: str, relation: str) -> str:
    raw = f"{source_node_id}|{target_node_id}|{relation}".encode("utf-8")
    return f"edge-{hashlib.sha1(raw).hexdigest()[:16]}"


def _normalize_existing_nodes(existing_nodes: list[dict[str, Any] | GraphNode]) -> list[dict[str, Any]]:
    nodes = []
    for node in existing_nodes:
        data = node.model_dump() if isinstance(node, GraphNode) else node
        label = str(data.get("label", "")).strip()
        node_id = str(data.get("id", "")).strip()
        if not label or not node_id:
            continue
        nodes.append(
            {
                "id": node_id,
                "label": label,
                "description": str(data.get("description", "")).strip(),
            }
        )
    return nodes


def build_graph_from_concepts(
    concept_sources: list[dict[str, Any]],
    api_key: str | None = None,
    model: str = "claude-sonnet-4-6",
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """
    Build a directed knowledge graph from concepts produced by concept extraction.

    Args:
        concept_sources: List of extraction payloads, each shaped like:
            {
              "source_file": str,
              "source_title": str,
              "concepts": [
                {"label": str, "description": str, ...}
              ]
            }
        api_key: Optional Anthropic key, otherwise env var is used.
        model: Claude model name.
    """
    nodes = _normalize_concept_sources(concept_sources)
    if not nodes:
        return [], []

    key = _get_api_key(api_key)
    edges = _detect_edges_with_llm(nodes, key, model)

    label_to_id = {node["label"]: node["id"] for node in nodes}
    graph_nodes = [
        GraphNode(
            id=node["id"],
            label=node["label"],
            description=node.get("description"),
            frequency=1,
        )
        for node in nodes
    ]

    graph_edges = []
    for edge in edges:
        src_id = label_to_id.get(edge["source"])
        tgt_id = label_to_id.get(edge["target"])
        if not src_id or not tgt_id:
            continue
        relation = edge.get("relation", "related to")
        strength = round(float(edge.get("strength", 0.5)), 4)
        graph_edges.append(
            GraphEdge(
                id=_edge_id(src_id, tgt_id, relation),
                source_node_id=src_id,
                target_node_id=tgt_id,
                relationship=relation,
                weight=strength,
            )
        )

    return graph_nodes, graph_edges


def extend_graph_with_concepts(
    concept_sources: list[dict[str, Any]],
    existing_nodes: list[dict[str, Any] | GraphNode],
    existing_edges: list[dict[str, Any] | GraphEdge],
    api_key: str | None = None,
    model: str = "claude-sonnet-4-6",
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """
    Incrementally extend an existing graph using newly extracted concepts.

    Returns merged nodes and merged edges (existing + newly detected).
    """
    normalized_existing_nodes = _normalize_existing_nodes(existing_nodes)
    new_nodes = _normalize_concept_sources(concept_sources)

    existing_labels = {node["label"] for node in normalized_existing_nodes}
    new_nodes = [node for node in new_nodes if node["label"] not in existing_labels]

    merged_node_dicts = normalized_existing_nodes + new_nodes
    merged_nodes = [
        GraphNode(
            id=node["id"],
            label=node["label"],
            description=node.get("description"),
            frequency=1,
        )
        for node in merged_node_dicts
    ]

    merged_edges: list[GraphEdge] = []
    seen_edge_ids = set()
    for edge in existing_edges:
        edge_model = edge if isinstance(edge, GraphEdge) else GraphEdge(**edge)
        merged_edges.append(edge_model)
        seen_edge_ids.add(edge_model.id)

    if not new_nodes:
        return merged_nodes, merged_edges

    key = _get_api_key(api_key)
    detected_edges = _detect_incremental_edges_with_llm(
        new_nodes=new_nodes,
        existing_nodes=normalized_existing_nodes,
        api_key=key,
        model=model,
    )

    label_to_id = {node["label"]: node["id"] for node in merged_node_dicts}
    for edge in detected_edges:
        src_id = label_to_id.get(edge["source"])
        tgt_id = label_to_id.get(edge["target"])
        if not src_id or not tgt_id:
            continue
        relation = edge.get("relation", "related to")
        edge_id = _edge_id(src_id, tgt_id, relation)
        if edge_id in seen_edge_ids:
            continue
        merged_edges.append(
            GraphEdge(
                id=edge_id,
                source_node_id=src_id,
                target_node_id=tgt_id,
                relationship=relation,
                weight=round(float(edge.get("strength", 0.5)), 4),
            )
        )
        seen_edge_ids.add(edge_id)

    return merged_nodes, merged_edges


def build_graph(card_ids: List[str]) -> tuple[List[GraphNode], List[GraphEdge]]:
    """Legacy placeholder graph builder kept for backward compatibility."""
    nodes = [GraphNode(id=f"node-{cid}", label=f"Card {cid}") for cid in card_ids]
    edges = [
        GraphEdge(
            id=f"edge-{idx}",
            source_node_id=nodes[idx].id,
            target_node_id=nodes[idx + 1].id,
            relationship="related_to",
            weight=1.0,
        )
        for idx in range(len(nodes) - 1)
    ]
    return nodes, edges
