from fastapi import APIRouter, HTTPException

from models.database import get_supabase
from models.schemas import Interaction

router = APIRouter()


@router.post("/interactions")
async def log_interaction(payload: Interaction):
    db = get_supabase()
    data = {
        "session_id": payload.session_id,
        "card_id": payload.card_id,
        "action": payload.action,
        "dwell_time_ms": payload.dwell_time_ms,
    }
    result = db.table("interactions").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to log interaction")
    return {"status": "logged", "card_id": payload.card_id, "action": payload.action}
