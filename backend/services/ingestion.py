"""
Card ingestion service.

Loads seed cards from JSON and serves them as the card catalogue.
In production this would pull from Supabase / scrapers.
"""

from __future__ import annotations

import json
import os
from typing import List

from models.schemas import Card

_SEED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "seed_cards.json")

# In-memory card store (loaded once)
_card_cache: List[Card] | None = None


def _load_seed_cards() -> List[Card]:
    with open(_SEED_PATH) as f:
        raw = json.load(f)
    return [Card(**item) for item in raw]


def get_all_cards() -> List[Card]:
    """Return the full card catalogue (cached in-memory)."""
    global _card_cache
    if _card_cache is None:
        _card_cache = _load_seed_cards()
    return list(_card_cache)  # return a copy


async def fetch_trending_cards(session_id: str) -> List[Card]:
    """Backwards-compatible async wrapper."""
    return get_all_cards()
