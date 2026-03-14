from typing import List

from models.schemas import Card


async def preprocess_cards(raw_cards: List[Card]) -> List[Card]:
    # Stub: in real flow, clean text, trim summaries, enrich keywords
    return raw_cards
