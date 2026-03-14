from fastapi import APIRouter, Query

from models.schemas import Card
from services.ingestion import fetch_trending_cards, get_all_cards
from services.preprocessing import preprocess_cards
from services.recommendation import rank_cards, recommend_cards
from services.swipe_store import get_liked_cards, get_swiped_ids

router = APIRouter()


@router.get("/cards", response_model=list[Card])
async def list_cards(session_id: str = Query(...)):
    raw = await fetch_trending_cards(session_id)
    cleaned = await preprocess_cards(raw)
    ranked = await rank_cards(cleaned)
    return ranked


@router.get("/cards/recommended", response_model=list[Card])
async def recommended_cards(session_id: str = Query(...)):
    """
    Personalised card feed.

    - Cold start (no swipe history): returns cards ranked by trending score.
    - With history: returns cards ranked by similarity to user profile + trending.
    - Always excludes already-swiped cards.
    """
    all_cards = get_all_cards()
    cleaned = await preprocess_cards(all_cards)
    liked = get_liked_cards(session_id)
    swiped = get_swiped_ids(session_id)
    return await recommend_cards(cleaned, liked, swiped)


@router.get("/cards/{card_id}", response_model=Card)
async def get_card(card_id: str, session_id: str = Query(...)):
    cards = await fetch_trending_cards(session_id)
    for card in cards:
        if card.id == card_id:
            return card
    return cards[0]
