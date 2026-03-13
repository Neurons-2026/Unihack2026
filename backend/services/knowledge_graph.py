from typing import List

from models.schemas import GraphEdge, GraphNode


def build_graph(card_ids: List[str]) -> tuple[List[GraphNode], List[GraphEdge]]:
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
