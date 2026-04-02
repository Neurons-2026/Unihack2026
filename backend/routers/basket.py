import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from deps import get_current_user
from models.database import get_supabase
from models.schemas import BasketItem

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/basket", response_model=list[BasketItem])
async def get_basket(
    session_id: str = Query(...),
    _user: dict = Depends(get_current_user),
):
    db = get_supabase()
    result = db.table("basket_items").select("*").eq("session_id", session_id).order("added_at").execute()
    return result.data or []


@router.post("/basket", response_model=BasketItem)
async def add_to_basket(
    item: BasketItem,
    _user: dict = Depends(get_current_user),
):
    db = get_supabase()
    data = {
        "id": item.id or str(uuid.uuid4()),
        "session_id": item.session_id,
        "card_id": item.card_id,
    }
    result = (
        db.table("basket_items")
        .upsert(data, on_conflict="session_id,card_id")
        .execute()
    )
    if not result.data:
        logger.error("Failed to upsert basket item for session %s", item.session_id)
        raise HTTPException(status_code=500, detail="Failed to add to basket")
    return result.data[0]


@router.delete("/basket/{item_id}")
async def remove_from_basket(
    item_id: str,
    _user: dict = Depends(get_current_user),
):
    db = get_supabase()
    db.table("basket_items").delete().eq("id", item_id).execute()
    return {"status": "removed", "item_id": item_id}
