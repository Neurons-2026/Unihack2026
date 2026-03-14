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

    def node_id(kw: str) -> str:
        return kw.replace(" ", "_").replace("-", "_")

    nodes = [
        GraphNode(
            id=node_id(kw),
            label=kw.title(),
            description=f"Appears in {count} article{'s' if count > 1 else ''}",
            frequency=count,
        )
        for kw, count in freq.items()
    ]

    edge_set: set[tuple[str, str]] = set()
    edges = []
    for card in cards:
        kws = list({kw.strip().lower() for kw in (card.keywords or []) if kw.strip()})
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


def _filter_largest_component(
    nodes: list[GraphNode], edges: list[GraphEdge]
) -> tuple[list[GraphNode], list[GraphEdge]]:
    if not nodes:
        return nodes, edges
    adj: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        adj[e.source_node_id].append(e.target_node_id)
        adj[e.target_node_id].append(e.source_node_id)
    visited: set[str] = set()
    components: list[set[str]] = []
    for nd in nodes:
        if nd.id not in visited:
            comp: set[str] = set()
            stack = [nd.id]
            while stack:
                cur = stack.pop()
                if cur in visited:
                    continue
                visited.add(cur)
                comp.add(cur)
                stack.extend(adj[cur])
            components.append(comp)
    largest = max(components, key=len)
    return (
        [n for n in nodes if n.id in largest],
        [e for e in edges if e.source_node_id in largest and e.target_node_id in largest],
    )


# Dummy concepts that bridge into the current AI graph
_DUMMY_NODES = [
    GraphNode(id="chain_of_thought", label="Chain Of Thought", description="Prompting technique for step-by-step reasoning", frequency=3),
    GraphNode(id="in_context_learning", label="In-Context Learning", description="Learning from examples in the prompt without weight updates", frequency=2),
    GraphNode(id="constitutional_ai", label="Constitutional AI", description="Framework for training AI systems with explicit behavioural principles", frequency=2),
    GraphNode(id="instruction_tuning", label="Instruction Tuning", description="Fine-tuning models to follow natural language instructions", frequency=2),
    GraphNode(id="knowledge_distillation", label="Knowledge Distillation", description="Training smaller models to mimic the outputs of larger ones", frequency=2),
    GraphNode(id="peft", label="PEFT", description="Parameter-efficient fine-tuning: adapting large models with minimal trainable parameters", frequency=2),
    GraphNode(id="lora", label="LoRA", description="Low-rank adaptation, a popular PEFT method", frequency=2),
    GraphNode(id="foundation_models", label="Foundation Models", description="Large pre-trained models adaptable to many downstream tasks", frequency=3),
]

# Edges within the dummy graph and bridges to existing nodes
_DUMMY_EDGES = [
    ("chain_of_thought", "reasoning"),
    ("chain_of_thought", "in_context_learning"),
    ("foundation_models", "instruction_tuning"),
    ("foundation_models", "peft"),
    ("foundation_models", "knowledge_distillation"),
    ("peft", "lora"),
    ("constitutional_ai", "safety"),
    ("constitutional_ai", "instruction_tuning"),
    ("instruction_tuning", "reward_models"),
    ("chain_of_thought", "llm_evals"),
    ("knowledge_distillation", "efficiency"),
]


@router.post("/graph/merge", response_model=GraphResponse)
async def merge_graph(session_id: str = Query("")):
    """Merge the current graph with a set of dummy concepts."""
    all_cards = await fetch_trending_cards(session_id)
    current_nodes, current_edges = _build_keyword_graph(all_cards)

    existing_ids = {n.id for n in current_nodes}
    new_nodes = [n for n in _DUMMY_NODES if n.id not in existing_ids]

    all_node_ids = existing_ids | {n.id for n in new_nodes}
    existing_edge_keys = {
        (min(e.source_node_id, e.target_node_id), max(e.source_node_id, e.target_node_id))
        for e in current_edges
    }
    new_edges = []
    for src, tgt in _DUMMY_EDGES:
        if src not in all_node_ids or tgt not in all_node_ids:
            continue
        key = (min(src, tgt), max(src, tgt))
        if key not in existing_edge_keys:
            existing_edge_keys.add(key)
            new_edges.append(GraphEdge(
                id=f"e_{key[0]}_{key[1]}",
                source_node_id=key[0],
                target_node_id=key[1],
                relationship="related_to",
                weight=1.0,
            ))

    merged_nodes = current_nodes + new_nodes
    merged_edges = current_edges + new_edges
    filtered_nodes, filtered_edges = _filter_largest_component(merged_nodes, merged_edges)
    return GraphResponse(nodes=filtered_nodes, edges=filtered_edges)


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
    # Try Supabase stored graph first
    try:
        from models.database import get_supabase

        supabase = get_supabase()
        nodes_res = supabase.table("graph_nodes").select("*").execute()
        edges_res = supabase.table("graph_edges").select("*").execute()

        if nodes_res.data and edges_res.data:
            nodes = [
                GraphNode(
                    id=n["id"],
                    label=n["label"],
                    description=n.get("description"),
                    frequency=n.get("frequency", 1),
                )
                for n in nodes_res.data
            ]
            edges = [
                GraphEdge(
                    id=str(e["id"]),
                    source_node_id=e["source_node_id"],
                    target_node_id=e["target_node_id"],
                    relationship=e.get("relationship", "related_to"),
                    weight=e.get("weight", 1.0),
                )
                for e in edges_res.data
            ]
            return GraphResponse(nodes=nodes, edges=edges)
    except Exception:
        pass

    # Fallback: build keyword graph from all trending cards
    all_cards = await fetch_trending_cards(session_id)
    nodes, edges = _build_keyword_graph(all_cards)
    return GraphResponse(nodes=nodes, edges=edges)
