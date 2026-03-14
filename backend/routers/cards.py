from fastapi import APIRouter, Query

from models.schemas import Card
from services.ingestion import fetch_trending_cards
from services.preprocessing import preprocess_cards
from services.recommendation import rank_cards

router = APIRouter()


@router.get("/cards", response_model=list[Card])
async def list_cards(session_id: str = Query(...)):
    raw = await fetch_trending_cards(session_id)
    cleaned = await preprocess_cards(raw)
    ranked = await rank_cards(cleaned)
    return ranked


@router.get("/cards/{card_id}", response_model=Card)
async def get_card(card_id: str, session_id: str = Query(...)):
    cards = await fetch_trending_cards(session_id)
    for card in cards:
        if card.id == card_id:
            return card
    return cards[0]
