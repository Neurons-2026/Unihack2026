import json
import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import get_settings
from routers import auth, basket, briefing, cards, graph, interactions

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
# Scheduled pipeline
# ---------------------------------------------------------------------------
MELBOURNE = ZoneInfo("Australia/Melbourne")


def _run_scheduled_pipeline():
    """Called by APScheduler — runs the full pipeline synchronously."""
    try:
        from services.pipeline import run_pipeline
        logger.info("Scheduled pipeline starting")
        summary = run_pipeline(
            sources=None,           # all sources
            generate_cards_flag=True,
            extract_concepts_flag=True,
            store_to_db=True,
            model="claude-sonnet-4-6",
        )
        logger.info("Scheduled pipeline finished: %s", summary)
    except Exception as exc:
        logger.exception("Scheduled pipeline failed: %s", exc)


def _purge_stale_briefings():
    """Called by APScheduler — deletes briefings older than 24 h."""
    try:
        from services.briefing import purge_stale_briefings
        purge_stale_briefings()
    except Exception as exc:
        logger.exception("Briefing purge failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler(timezone=MELBOURNE)
    # 9:00 AM Melbourne every day
    scheduler.add_job(
        _run_scheduled_pipeline,
        CronTrigger(hour=9, minute=0, timezone=MELBOURNE),
        id="pipeline_morning",
        replace_existing=True,
    )
    # 5:30 PM Melbourne every day
    scheduler.add_job(
        _run_scheduled_pipeline,
        CronTrigger(hour=17, minute=30, timezone=MELBOURNE),
        id="pipeline_afternoon",
        replace_existing=True,
    )
    # Midnight Melbourne — purge briefings older than 24 h
    scheduler.add_job(
        _purge_stale_briefings,
        CronTrigger(hour=0, minute=0, timezone=MELBOURNE),
        id="briefing_purge",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Pipeline scheduler started — jobs: %s",
        [str(j.next_run_time) for j in scheduler.get_jobs()],
    )
    yield
    scheduler.shutdown(wait=False)
    logger.info("Pipeline scheduler stopped")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="10min AI Daily API", version="0.2.0", lifespan=lifespan)

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
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
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
