from typing import List, Optional
from pydantic import BaseModel, HttpUrl


class Card(BaseModel):
    id: str
    card_title: str
    card_summary: str
    keywords: List[str]
    source: str
    source_url: Optional[HttpUrl] = None
    thumbnail_keyword: Optional[str] = None
    image_url: Optional[str] = None
    trending_score: Optional[float] = None


class Interaction(BaseModel):
    session_id: str
    card_id: str
    action: str
    dwell_time_ms: Optional[int] = None


class BasketItem(BaseModel):
    id: str
    session_id: str
    card_id: str
    added_at: Optional[str] = None


class BriefingRequest(BaseModel):
    session_id: str
    card_ids: List[str]


class BriefingResponse(BaseModel):
    id: str
    content: str
    reading_time_min: Optional[float] = None


class GraphNode(BaseModel):
    id: str
    label: str
    description: Optional[str] = None
    frequency: Optional[int] = None
    is_today: Optional[bool] = None


class GraphEdge(BaseModel):
    id: str
    source_node_id: str
    target_node_id: str
    relationship: Optional[str] = "related_to"
    weight: Optional[float] = None


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
