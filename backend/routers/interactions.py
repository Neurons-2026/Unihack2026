from fastapi import APIRouter

from models.schemas import Interaction
from services.swipe_store import record_interaction

router = APIRouter()


@router.post("/interactions")
async def log_interaction(payload: Interaction):
    record_interaction(payload)
    return {"status": "logged", "card_id": payload.card_id, "action": payload.action}
