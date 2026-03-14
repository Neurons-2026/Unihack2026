import json
import os
from pathlib import Path

from fastapi import APIRouter, Query, Request
from typing import List

from models.schemas import Card
from services.ingestion import fetch_trending_cards
from services.preprocessing import preprocess_cards
from services.recommendation import rank_cards

router = APIRouter()

_briefing_images_path = Path(__file__).parent.parent / "data" / "briefing_images.json"


def _load_briefing_images() -> dict[str, str]:
    """Load briefing landscape image mapping fresh each call."""
    if _briefing_images_path.exists():
        return json.loads(_briefing_images_path.read_text())
    return {}


_static_root = Path(__file__).parent.parent / "static"


def _full_image_url(url: str, request: Request) -> str:
    """Convert local /static/... paths to full URLs with cache-busting."""
    if url and url.startswith("/static/"):
        full = f"{request.base_url.scheme}://{request.base_url.netloc}{url}"
        # Append file mtime so the browser re-fetches when the image changes
        local_path = _static_root / url.removeprefix("/static/")
        if local_path.exists():
            mtime = int(os.path.getmtime(local_path))
            full += f"?v={mtime}"
        return full
    return url


@router.get("/cards", response_model=list[Card])
async def list_cards(session_id: str = Query(...)):
    raw = await fetch_trending_cards(session_id)
    cleaned = await preprocess_cards(raw)
    ranked = await rank_cards(cleaned)
    return ranked


@router.get("/cards/feed", response_model=List[dict])
async def get_card_feed(request: Request):
    """Fetch all preprocessed cards from Supabase with image URLs.

    Returns cards in the format the frontend expects (CardData shape).
    """
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    from models.database import get_supabase

    db = get_supabase()

    # Fetch cards with their content_item data for source info
    cards_result = db.table("cards").select("*").execute()
    items_result = db.table("content_items").select("id, source, source_url, title, fetched_at").execute()

    items_by_id = {i["id"]: i for i in items_result.data}
    briefing_images = _load_briefing_images()

    feed = []
    for card in cards_result.data:
        cid = card["id"]
        item = items_by_id.get(cid, {})

        # Map source names to frontend source types
        source_raw = item.get("source", card.get("source", ""))
        source_map = {
            "github_trending": "github",
            "huggingface_papers": "huggingface",
            "openai_news": "openai_blog",
            "anthropic_news": "anthropic_blog",
        }
        source = source_map.get(source_raw, source_raw)

        feed.append({
            "id": cid,
            "source": source,
            "title": card.get("card_title", ""),
            "description": card.get("card_summary", ""),
            "keywords": card.get("keywords", []),
            "sourceUrl": item.get("source_url", ""),
            "publishedDate": (item.get("fetched_at", "") or "")[:10],
            "imageUrl": _full_image_url(card.get("image_url", ""), request),
            "briefingImageUrl": _full_image_url(briefing_images.get(cid, ""), request),
            "metadata": {},
        })

    return feed


@router.get("/cards/{card_id}", response_model=Card)
async def get_card(card_id: str, session_id: str = Query(...)):
    cards = await fetch_trending_cards(session_id)
    for card in cards:
        if card.id == card_id:
            return card
    return cards[0]
