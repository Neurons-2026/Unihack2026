from functools import lru_cache
from typing import List

from supabase import create_client, Client

from config import get_settings
from models.schemas import Card


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in environment")
    return create_client(settings.supabase_url, settings.supabase_key)


def get_cards_from_db(limit: int = 20) -> List[Card]:
    """Fetch cards from Supabase, ordered by trending_score desc."""
    supabase = get_supabase()
    response = supabase.table("cards").select("*").order("trending_score", desc=True).limit(limit).execute()
    cards_data = response.data
    cards = []
    for data in cards_data:
        # Map DB fields to Card model
        card = Card(
            id=data["id"],
            card_title=data["card_title"],
            card_summary=data["card_summary"],
            keywords=data["keywords"],
            thumbnail_keyword=data["thumbnail_keyword"],
            source="db",  # Placeholder, could fetch from content_items
            source_url=None,  # Placeholder
            trending_score=data["trending_score"],
        )
        cards.append(card)
    return cards
