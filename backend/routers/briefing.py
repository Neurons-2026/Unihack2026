from fastapi import APIRouter

from models.schemas import BriefingRequest, BriefingResponse
from services.briefing import generate_briefing

router = APIRouter()


@router.post("/briefing/generate", response_model=BriefingResponse)
async def create_briefing(request: BriefingRequest):
    return await generate_briefing(request.session_id, request.card_ids)


@router.get("/briefing/{briefing_id}", response_model=BriefingResponse)
async def get_briefing(briefing_id: str):
    return BriefingResponse(id=briefing_id, content="Cached briefing not yet implemented")
