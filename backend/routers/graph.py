from collections import defaultdict

from fastapi import APIRouter, Body, Query

from models.schemas import GraphEdge, GraphNode, GraphResponse
from services.ingestion import fetch_trending_cards

router = APIRouter()


def _build_keyword_graph(cards):
    """Build a keyword co-occurrence graph from a list of cards."""
    freq: dict[str, int] = defaultdict(int)
    for card in cards:
        seen: set[str] = set()
        for kw in (card.keywords or []):
            kw_norm = kw.strip().lower()
            if kw_norm and kw_norm not in seen:
                freq[kw_norm] += 1
                seen.add(kw_norm)

    if not freq:
        return [], []

    # Keep only keywords that appear in 2+ cards; fall back to top-8 if too few
    min_freq = 2
    filtered = {kw: c for kw, c in freq.items() if c >= min_freq}
    if len(filtered) < 5:
        filtered = dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)[:8])

    def node_id(kw: str) -> str:
        return kw.replace(" ", "_").replace("-", "_")

    nodes = [
        GraphNode(
            id=node_id(kw),
            label=kw.title(),
            description=f"Appears in {count} article{'s' if count > 1 else ''}",
            frequency=count,
        )
        for kw, count in filtered.items()
    ]

    kept_ids = {node_id(kw) for kw in filtered}

    edge_set: set[tuple[str, str]] = set()
    edges = []
    for card in cards:
        kws = [kw.strip().lower() for kw in (card.keywords or []) if kw.strip() and node_id(kw.strip().lower()) in kept_ids]
        kws = list(dict.fromkeys(kws))  # deduplicate preserving order
        for i in range(len(kws)):
            for j in range(i + 1, len(kws)):
                a, b = node_id(kws[i]), node_id(kws[j])
                key = (min(a, b), max(a, b))
                if key not in edge_set:
                    edge_set.add(key)
                    edges.append(
                        GraphEdge(
                            id=f"e_{key[0]}_{key[1]}",
                            source_node_id=key[0],
                            target_node_id=key[1],
                            relationship="co-occurs",
                            weight=1.0,
                        )
                    )

    # Keep only the largest connected component
    adj: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        adj[e.source_node_id].append(e.target_node_id)
        adj[e.target_node_id].append(e.source_node_id)

    visited: set[str] = set()
    components: list[set[str]] = []
    for n in [nd.id for nd in nodes]:
        if n not in visited:
            comp: set[str] = set()
            stack = [n]
            while stack:
                cur = stack.pop()
                if cur in visited:
                    continue
                visited.add(cur)
                comp.add(cur)
                stack.extend(adj[cur])
            components.append(comp)

    largest = max(components, key=len)
    nodes = [n for n in nodes if n.id in largest]
    edges = [e for e in edges if e.source_node_id in largest and e.target_node_id in largest]

    return nodes, edges


@router.post("/graph/generate", response_model=GraphResponse)
async def generate_graph(
    card_ids: list[str] = Body(...),
    session_id: str = Query(""),
):
    all_cards = await fetch_trending_cards(session_id)
    card_map = {c.id: c for c in all_cards}
    cards = [card_map[cid] for cid in card_ids if cid in card_map]
    if not cards:
        cards = all_cards
    nodes, edges = _build_keyword_graph(cards)
    return GraphResponse(nodes=nodes, edges=edges)


@router.get("/graph", response_model=GraphResponse)
async def get_graph(session_id: str = Query(...)):
    all_cards = await fetch_trending_cards(session_id)
    nodes, edges = _build_keyword_graph(all_cards)
    return GraphResponse(nodes=nodes, edges=edges)
