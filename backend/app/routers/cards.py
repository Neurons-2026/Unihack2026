from datetime import datetime
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Card(BaseModel):
    id: str
    title: str
    summary: str
    source: str
    url: str
    timestamp: datetime


@router.get("/", response_model=List[Card])
def list_cards() -> List[Card]:
    # Placeholder feed to unblock frontend integration during hackathon setup
    now = datetime.utcnow()
    return [
        Card(
            id="demo-1",
            title="New Transformer Variant", 
            summary="Paper claims improved efficiency on long context windows.",
            source="huggingface",
            url="https://huggingface.co/papers",
            timestamp=now,
        ),
        Card(
            id="demo-2",
            title="GitHub Trending: fast-llm-eval",
            summary="Tooling to benchmark small LLMs quickly.",
            source="github",
            url="https://github.com/trending",
            timestamp=now,
        ),
    ]
