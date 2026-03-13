from typing import List

from models.schemas import BriefingResponse


async def generate_briefing(session_id: str, card_ids: List[str]) -> BriefingResponse:
    # Stub content; replace with Anthropic call and prompt from agent instructions
    content = "\n".join([f"- Card {cid}: summary pending" for cid in card_ids])
    return BriefingResponse(id=f"briefing-{session_id}", content=content, reading_time_min=10.0)
