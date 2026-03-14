import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json

from config import get_settings
from routers import basket, briefing, cards, graph, interactions

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title="10min AI Daily API", version="0.2.0")

cors_origins = []
if settings.cors_origins:
    try:
        cors_origins = json.loads(settings.cors_origins)
    except:
        cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cards.router, prefix="/api/v1", tags=["cards"])
app.include_router(interactions.router, prefix="/api/v1", tags=["interactions"])
app.include_router(basket.router, prefix="/api/v1", tags=["basket"])
app.include_router(briefing.router, prefix="/api/v1", tags=["briefing"])
app.include_router(graph.router, prefix="/api/v1", tags=["graph"])

try:
    from routers import concepts

    app.include_router(concepts.router, prefix="/api/v1", tags=["concepts"])
except Exception as exc:
    logger.warning("Concepts router disabled: %s", exc)

try:
    from routers import pipeline

    app.include_router(pipeline.router, prefix="/api/v1", tags=["pipeline"])
except Exception as exc:
    logger.warning("Pipeline router disabled: %s", exc)


static_dir = Path(__file__).parent / "static" / "images"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
