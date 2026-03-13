import uuid

from fastapi import APIRouter, HTTPException, Query

from models.database import get_supabase
from models.schemas import BasketItem

router = APIRouter()


@router.get("/basket", response_model=list[BasketItem])
async def get_basket(session_id: str = Query(...)):
    db = get_supabase()
    result = db.table("basket_items").select("*").eq("session_id", session_id).order("added_at").execute()
    return result.data or []


@router.post("/basket", response_model=BasketItem)
async def add_to_basket(item: BasketItem):
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
        raise HTTPException(status_code=500, detail="Failed to add to basket")
    return result.data[0]


@router.delete("/basket/{item_id}")
async def remove_from_basket(item_id: str):
    db = get_supabase()
    db.table("basket_items").delete().eq("id", item_id).execute()
    return {"status": "removed", "item_id": item_id}
