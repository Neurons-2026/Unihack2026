from typing import List

from models.schemas import Card


async def rank_cards(cards: List[Card]) -> List[Card]:
    # Stub: sort by trending_score descending
    return sorted(cards, key=lambda c: c.trending_score or 0, reverse=True)
