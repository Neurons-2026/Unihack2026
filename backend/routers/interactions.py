import logging

from fastapi import APIRouter, Depends, HTTPException, Query

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


@router.get("/stats")
async def get_swipe_stats(
    session_id: str = Query(...),
    _user: dict = Depends(get_current_user),
):
    """Return cumulative swipe counts for a session/user."""
    db = get_supabase()
    result = db.table("user_stats").select("*").eq("session_id", session_id).execute()
    if not result.data:
        return {"session_id": session_id, "total_swipes": 0, "swipes_right": 0, "swipes_left": 0}
    row = result.data[0]
    return {
        "session_id": session_id,
        "total_swipes": row["total_swipes"],
        "swipes_right": row["swipes_right"],
        "swipes_left": row["swipes_left"],
        "last_swiped_at": row.get("last_swiped_at"),
    }
