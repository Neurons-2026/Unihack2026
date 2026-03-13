"""Lightweight worker stub for ingestion + preprocessing.

Run locally with `python backend/worker/worker.py` while services are stubs.
"""

import asyncio
import logging

from services.ingestion import fetch_trending_cards
from services.preprocessing import preprocess_cards
from services.recommendation import rank_cards

logger = logging.getLogger("worker")
logging.basicConfig(level=logging.INFO)


async def run_cycle():
    cards = await fetch_trending_cards("worker")
    cleaned = await preprocess_cards(cards)
    ranked = await rank_cards(cleaned)
    logger.info("cycle_complete", extra={"items": len(ranked)})


if __name__ == "__main__":
    asyncio.run(run_cycle())
