import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from deps import get_current_user
from models.database import get_supabase
from models.schemas import BriefingRequest, BriefingResponse
from services.briefing import generate_briefing, generate_briefing_stream

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/briefing/generate", response_model=BriefingResponse)
async def create_briefing(
    request: BriefingRequest,
    _user: dict = Depends(get_current_user),
):
    """Generate a briefing (non-streaming). Returns full content at once."""
    return await generate_briefing(request.session_id, request.card_ids)


@router.post("/briefing/generate/stream")
async def create_briefing_stream(
    request: BriefingRequest,
    _user: dict = Depends(get_current_user),
):
    """Generate a briefing with streaming. Returns text chunks as they are generated."""
    return StreamingResponse(
        generate_briefing_stream(request.session_id, request.card_ids),
        media_type="text/plain",
    )


@router.get("/briefing/{briefing_id}", response_model=BriefingResponse)
async def get_briefing(briefing_id: str, _user: dict = Depends(get_current_user)):
    """Retrieve a cached briefing by ID."""
    db = get_supabase()
    result = db.table("briefings").select("*").eq("id", briefing_id).limit(1).execute()

    if result.data:
        row = result.data[0]
        return BriefingResponse(
            id=briefing_id,
            content=row["content"],
            reading_time_min=row.get("reading_time_min"),
        )

    return BriefingResponse(id=briefing_id, content="Briefing not found.", reading_time_min=0)
