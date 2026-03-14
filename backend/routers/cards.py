from fastapi import APIRouter, Query

from models.database import get_cards_from_db
from models.schemas import Card
from services.recommendation import rank_cards

router = APIRouter()


@router.get("/cards", response_model=list[Card])
async def list_cards(session_id: str = Query(...)):
    cards = get_cards_from_db(limit=20)
    ranked = await rank_cards(cards)
    return ranked


@router.get("/cards/{card_id}", response_model=Card)
async def get_card(card_id: str, session_id: str = Query(...)):
    cards = get_cards_from_db(limit=20)
    for card in cards:
        if card.id == card_id:
            return card
    return cards[0] if cards else None
