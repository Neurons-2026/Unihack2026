from fastapi import APIRouter, Query

from models.schemas import BasketItem

router = APIRouter()


@router.get("/basket", response_model=list[BasketItem])
async def get_basket(session_id: str = Query(...)):
    return []


@router.post("/basket", response_model=BasketItem)
async def add_to_basket(item: BasketItem):
    return item


@router.delete("/basket/{item_id}")
async def remove_from_basket(item_id: str):
    return {"status": "removed", "item_id": item_id}
