"""Lightweight worker stub for scraping and briefing generation tasks.

Replace the placeholder logic with real scraping, enrichment, and LLM calls.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
import os

import structlog

logger = structlog.get_logger()

SCRAPE_SOURCES = os.getenv("SCRAPE_SOURCES", "github_trending,huggingface_models").split(",")


async def fetch_github_trending() -> list[dict]:
    # Placeholder that simulates fetch; replace with real scraping/API calls
    logger.info("fetch_github_trending.start")
    await asyncio.sleep(0.1)
    return [
        {
            "id": "gh-demo",
            "title": "example repo",
            "url": "https://github.com/example/repo",
            "source": "github",
            "timestamp": datetime.utcnow().isoformat(),
        }
    ]


async def fetch_huggingface_models() -> list[dict]:
    logger.info("fetch_huggingface_models.start")
    await asyncio.sleep(0.1)
    return [
        {
            "id": "hf-demo",
            "title": "example model",
            "url": "https://huggingface.co/models",
            "source": "huggingface",
            "timestamp": datetime.utcnow().isoformat(),
        }
    ]


async def run_cycle():
    logger.info("worker.cycle.start", sources=SCRAPE_SOURCES)
    tasks = []
    if "github_trending" in SCRAPE_SOURCES:
        tasks.append(fetch_github_trending())
    if "huggingface_models" in SCRAPE_SOURCES:
        tasks.append(fetch_huggingface_models())

    results = []
    if tasks:
        results_nested = await asyncio.gather(*tasks)
        for chunk in results_nested:
            results.extend(chunk)

    logger.info("worker.cycle.complete", items=len(results))
    # TODO: persist to DB, push to Redis queue, or call API endpoint


if __name__ == "__main__":
    try:
        asyncio.run(run_cycle())
    except KeyboardInterrupt:
        logger.warning("worker.shutdown")
