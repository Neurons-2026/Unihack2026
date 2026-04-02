import json
import logging
import sys
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import get_settings
from routers import basket, briefing, cards, graph, interactions

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Settings & startup validation
# ---------------------------------------------------------------------------
settings = get_settings()

_required = {"supabase_url": settings.supabase_url, "supabase_key": settings.supabase_key, "anthropic_api_key": settings.anthropic_api_key}
for name, value in _required.items():
    if not value:
        logger.warning("Config warning: %s is not set", name.upper())

if settings.app_env == "production" and not settings.supabase_jwt_secret:
    logger.warning("Config warning: SUPABASE_JWT_SECRET is not set — auth will not work in production")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="10min AI Daily API", version="0.2.0")

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
cors_origins = ["*"]
if settings.cors_origins:
    try:
        cors_origins = json.loads(settings.cors_origins)
    except Exception:
        cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s %d %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response

# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
static_dir = Path(__file__).parent / "static" / "images"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
