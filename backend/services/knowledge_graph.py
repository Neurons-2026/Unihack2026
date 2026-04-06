"""
Knowledge graph builder — algorithmic edge detection.

Edges are detected using TF-IDF cosine similarity on concept
label + description text.  Relationship types are inferred from
concept categories.  No LLM calls are made.
"""

import hashlib
import logging
from typing import Any, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from models.schemas import GraphEdge, GraphNode

logger = logging.getLogger(__name__)

# Minimum cosine similarity to create an edge.
# Concept descriptions are often short so scores stay low — 0.05 captures
# meaningful token overlap without being too noisy.
SIMILARITY_THRESHOLD = 0.05

# Category → rough semantic tier (lower tier "enables" higher tier)
_CATEGORY_TIER: dict[str, int] = {
    "dataset":      0,
    "benchmark":    0,
    "theory":       1,
    "technique":    2,
    "architecture": 2,
    "tool":         3,
    "application":  4,
}

# Relation rules: (source_tier, target_tier) → relation label
# Checked in order; first match wins.  Falls back to "related to".
_TIER_RELATIONS: list[tuple[tuple[int, int], str]] = [
    ((0, 2), "evaluates"),   # dataset/benchmark → technique
    ((0, 3), "evaluates"),   # dataset/benchmark → tool
    ((1, 2), "enables"),     # theory → technique
    ((1, 3), "enables"),     # theory → tool
    ((2, 3), "enables"),     # technique → tool
    ((2, 4), "enables"),     # technique → application
    ((3, 4), "enables"),     # tool → application
]


def _infer_relation(cat_a: str, cat_b: str) -> tuple[str, str, str]:
    """
    Return (source_label, target_label, relation) given two categories.
    source → target direction follows semantic tier ordering.
    """
    tier_a = _CATEGORY_TIER.get(cat_a, 2)
    tier_b = _CATEGORY_TIER.get(cat_b, 2)

    for (ta, tb), rel in _TIER_RELATIONS:
        if tier_a == ta and tier_b == tb:
            return "a", "b", rel
        if tier_b == ta and tier_a == tb:
            return "b", "a", rel  # reversed direction

    # Same tier or no rule found
    if cat_a == cat_b:
        return "a", "b", "competes with"
    return "a", "b", "related to"


def _edge_id(source_node_id: str, target_node_id: str, relation: str) -> str:
    raw = f"{source_node_id}|{target_node_id}|{relation}".encode("utf-8")
    return f"edge-{hashlib.sha1(raw).hexdigest()[:16]}"


def _concept_text(node: dict[str, Any]) -> str:
    """Build the text representation used for TF-IDF."""
    parts = [
        node.get("label", ""),
        node.get("description", ""),
        node.get("why_innovative", ""),
        node.get("impact_on_applications", ""),
    ]
    return " ".join(p for p in parts if p).lower()


def _normalize_concept_sources(concept_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for source in concept_sources:
        source_file = str(source.get("source_file", "unknown")).strip() or "unknown"
        source_title = str(source.get("source_title", source_file)).strip() or source_file
        for concept in source.get("concepts", []):
            label = str(concept.get("label", "")).strip()
            if not label:
                continue
            nodes.append({
                "id": f"{source_file}::{label}",
                "label": label,
                "description": str(concept.get("description", "")).strip(),
                "why_innovative": str(concept.get("why_innovative", "")).strip(),
                "impact_on_applications": str(concept.get("impact_on_applications", "")).strip(),
                "category": str(concept.get("category", "")).strip(),
                "relevance_score": float(concept.get("relevance_score", 0.0)),
                "source_file": source_file,
                "source_title": source_title,
            })
    return nodes


def _detect_edges(
    nodes: list[dict[str, Any]],
    threshold: float = SIMILARITY_THRESHOLD,
    only_involving: Optional[set] = None,
) -> list[GraphEdge]:
    """
    Compute TF-IDF cosine similarity for all concept pairs and return
    edges whose similarity meets the threshold.

    Args:
        nodes: All concept nodes (new + existing).
        threshold: Minimum similarity to add an edge.
        only_involving: If set, only emit edges where at least one
                        node id is in this set (used for incremental updates).
    """
    if len(nodes) < 2:
        return []

    texts = [_concept_text(n) for n in nodes]

    try:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        sim_matrix = cosine_similarity(tfidf_matrix)
    except Exception as exc:
        logger.warning("TF-IDF vectorisation failed: %s", exc)
        return []

    edges: list[GraphEdge] = []
    seen: set[str] = set()

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            score = float(sim_matrix[i, j])
            if score < threshold:
                continue

            node_a = nodes[i]
            node_b = nodes[j]

            if only_involving and (
                node_a["id"] not in only_involving
                and node_b["id"] not in only_involving
            ):
                continue

            direction, _, relation = _infer_relation(
                node_a.get("category", ""),
                node_b.get("category", ""),
            )

            if direction == "a":
                src_id, tgt_id = node_a["id"], node_b["id"]
            else:
                src_id, tgt_id = node_b["id"], node_a["id"]

            eid = _edge_id(src_id, tgt_id, relation)
            if eid in seen:
                continue
            seen.add(eid)

            edges.append(GraphEdge(
                id=eid,
                source_node_id=src_id,
                target_node_id=tgt_id,
                relationship=relation,
                weight=round(score, 4),
            ))

    logger.info("Detected %d edges from %d concepts (threshold=%.2f)", len(edges), len(nodes), threshold)
    return edges


def _normalize_existing_nodes(existing_nodes: List) -> list[dict[str, Any]]:
    nodes = []
    for node in existing_nodes:
        data = node.model_dump() if isinstance(node, GraphNode) else node
        label = str(data.get("label", "")).strip()
        node_id = str(data.get("id", "")).strip()
        if not label or not node_id:
            continue
        nodes.append({
            "id": node_id,
            "label": label,
            "description": str(data.get("description", "")).strip(),
            "category": str(data.get("category", "")).strip(),
            "why_innovative": "",
            "impact_on_applications": "",
        })
    return nodes


def build_graph_from_concepts(
    concept_sources: list[dict[str, Any]],
    api_key: Optional[str] = None,   # kept for signature compatibility, unused
    model: str = "claude-sonnet-4-6",  # kept for signature compatibility, unused
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """
    Build a directed knowledge graph from concepts using TF-IDF cosine similarity.
    """
    nodes = _normalize_concept_sources(concept_sources)
    if not nodes:
        return [], []

    graph_nodes = [
        GraphNode(
            id=node["id"],
            label=node["label"],
            description=node.get("description"),
            frequency=1,
        )
        for node in nodes
    ]

    graph_edges = _detect_edges(nodes)
    return graph_nodes, graph_edges


def extend_graph_with_concepts(
    concept_sources: list[dict[str, Any]],
    existing_nodes: List,
    existing_edges: List,
    api_key: Optional[str] = None,   # kept for signature compatibility, unused
    model: str = "claude-sonnet-4-6",  # kept for signature compatibility, unused
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """
    Incrementally extend an existing graph with newly extracted concepts.
    Only computes edges that involve at least one new node.
    """
    normalized_existing = _normalize_existing_nodes(existing_nodes)
    new_nodes = _normalize_concept_sources(concept_sources)

    existing_labels = {n["label"] for n in normalized_existing}
    new_nodes = [n for n in new_nodes if n["label"] not in existing_labels]

    all_nodes = normalized_existing + new_nodes
    merged_nodes = [
        GraphNode(
            id=n["id"],
            label=n["label"],
            description=n.get("description"),
            frequency=1,
        )
        for n in all_nodes
    ]

    # Carry forward existing edges
    merged_edges: list[GraphEdge] = []
    seen_edge_ids: set[str] = set()
    for edge in existing_edges:
        e = edge if isinstance(edge, GraphEdge) else GraphEdge(**edge)
        merged_edges.append(e)
        seen_edge_ids.add(e.id)

    if not new_nodes:
        return merged_nodes, merged_edges

    new_ids = {n["id"] for n in new_nodes}
    new_edges = _detect_edges(all_nodes, only_involving=new_ids)

    for edge in new_edges:
        if edge.id not in seen_edge_ids:
            merged_edges.append(edge)
            seen_edge_ids.add(edge.id)

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
