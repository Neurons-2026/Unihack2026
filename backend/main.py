from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import basket, briefing, cards, concepts, graph, interactions

settings = get_settings()

app = FastAPI(title="10min AI Daily API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.cors_origins] if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cards.router, prefix="/api/v1", tags=["cards"])
app.include_router(interactions.router, prefix="/api/v1", tags=["interactions"])
app.include_router(basket.router, prefix="/api/v1", tags=["basket"])
app.include_router(briefing.router, prefix="/api/v1", tags=["briefing"])
app.include_router(graph.router, prefix="/api/v1", tags=["graph"])
app.include_router(concepts.router, prefix="/api/v1", tags=["concepts"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
