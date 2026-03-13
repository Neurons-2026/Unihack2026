from fastapi import APIRouter, Query

from models.schemas import GraphResponse
from services.knowledge_graph import build_graph

router = APIRouter()


@router.post("/graph/generate", response_model=GraphResponse)
async def generate_graph(card_ids: list[str]):
    nodes, edges = build_graph(card_ids)
    return GraphResponse(nodes=nodes, edges=edges)


@router.get("/graph", response_model=GraphResponse)
async def get_graph(session_id: str = Query(...)):
    # Placeholder graph until we merge real data
    nodes, edges = build_graph(["seed-1", "seed-2"])
    return GraphResponse(nodes=nodes, edges=edges)
