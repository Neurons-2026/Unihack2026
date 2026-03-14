from fastapi import APIRouter

from models.schemas import Interaction

router = APIRouter()


@router.post("/interactions")
async def log_interaction(payload: Interaction):
    # TODO: persist to Supabase user_actions
    return {"status": "logged", "card_id": payload.card_id, "action": payload.action}
