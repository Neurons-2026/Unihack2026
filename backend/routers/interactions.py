import logging

from fastapi import APIRouter, Depends, HTTPException

from deps import get_current_user
from models.database import get_supabase
from models.schemas import Interaction

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/interactions")
async def log_interaction(
    payload: Interaction,
    _user: dict = Depends(get_current_user),
):
    db = get_supabase()
    data = {
        "session_id": payload.session_id,
        "card_id": payload.card_id,
        "action": payload.action,
        "dwell_time_ms": payload.dwell_time_ms,
    }
    result = db.table("interactions").insert(data).execute()
    if not result.data:
        logger.error("Failed to log interaction for session %s card %s", payload.session_id, payload.card_id)
        raise HTTPException(status_code=500, detail="Failed to log interaction")
    return {"status": "logged", "card_id": payload.card_id, "action": payload.action}
