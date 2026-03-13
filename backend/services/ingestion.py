from datetime import datetime
from typing import List

from models.schemas import Card


async def fetch_trending_cards(session_id: str) -> List[Card]:
    # TODO: Replace with real scraping and Supabase persistence
    now = datetime.utcnow().isoformat()
    return [
        Card(
            id="seed-1",
            card_title="New model tops long-context benchmark",
            card_summary="A lightweight transformer variant improves efficiency for 32k tokens.",
            keywords=["transformer", "long context", "research"],
            source="huggingface",
            source_url="https://huggingface.co/papers",
            thumbnail_keyword="context",
            trending_score=0.8,
        ),
        Card(
            id="seed-2",
            card_title="GitHub trending: eval toolkit",
            card_summary="Open-source harness to benchmark small LLMs quickly.",
            keywords=["github", "eval", "tooling"],
            source="github",
            source_url="https://github.com/trending",
            thumbnail_keyword="eval",
            trending_score=0.6,
        ),
    ]
