import asyncio
import json
from pathlib import Path
from typing import List

from models.database import get_supabase
from models.schemas import Card
from services.scrapers.github_trending import scrape_github_trending

SEED_CARDS_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_cards.json"


def _load_seed_cards(limit: int = 20) -> List[Card]:
    data = json.loads(SEED_CARDS_PATH.read_text(encoding="utf-8"))
    return [Card(**item) for item in data[:limit]]


def _to_provisional_card(item: dict) -> Card:
    metadata = item.get("metadata") or {}
    ranking = item.get("ranking") or {}
    language = (metadata.get("language") or "github").lower()
    raw_summary = item.get("raw_summary") or item.get("title") or "Trending repository"
    card_summary = raw_summary if len(raw_summary) <= 120 else raw_summary[:117].rstrip() + "..."
    return Card(
        id=item["id"],
        card_title=f"GitHub trending: {item.get('title', item['id'])}",
        card_summary=card_summary,
        keywords=[language],
        source=item["source"],
        source_url=item["source_url"],
        thumbnail_keyword=language,
        trending_score=ranking.get("source_rank_score", ranking.get("trending_score", 0.0)),
    )


def _load_cards_from_supabase(limit: int = 50) -> List[Card]:
    db = get_supabase()
    result = (
        db.table("cards")
        .select("id,card_title,card_summary,keywords,source,source_url,thumbnail_keyword,image_url,trending_score")
        .order("trending_score", desc=True)
        .limit(limit)
        .execute()
    )

    rows = result.data or []
    cards: List[Card] = []
    for row in rows:
        try:
            cards.append(Card(**row))
        except Exception:
            continue
    return cards


async def fetch_trending_cards(session_id: str) -> List[Card]:
    # Primary path: use cards already stored in Supabase.
    try:
        db_cards = await asyncio.to_thread(_load_cards_from_supabase, 50)
        if db_cards:
            return db_cards
    except Exception:
        pass

    # Fast fallback for demo reliability.
    try:
        seed_cards = _load_seed_cards(limit=20)
        if seed_cards:
            return seed_cards
    except Exception:
        pass

    # Scrape latest GitHub trending repos and enrich each with README text.
    # If scraping fails (network/layout/rate-limit), fallback to seed dataset.
    try:
        scraped = await asyncio.to_thread(scrape_github_trending, 20, True)
        cards = [_to_provisional_card(item) for item in scraped]
        if cards:
            return cards
    except Exception:
        pass

    return _load_seed_cards(limit=20)
