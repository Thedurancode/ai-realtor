"""RealtorClaw API — AI-Powered Real Estate Platform."""

from app.logging_config import setup_logging
setup_logging()

import asyncio
import logging
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.config import settings
from app.database import SessionLocal
from app.rate_limit import limiter, RateLimitToggleMiddleware, RATE_LIMIT_ENABLED, RATE_LIMIT_DEFAULT, RATE_LIMIT_TIERS
from app.auth import verify_api_key
from app.middleware.api_key import ApiKeyMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.websocket import manager
from app.api_key_cache import invalidate_api_key_cache
from app.routers.registry import register_routers
from app.middleware.error_handler import register_error_handlers
from app.middleware.metrics import MetricsMiddleware, metrics_endpoint, PROMETHEUS_AVAILABLE

import app.models  # noqa: F401 — ensure all models are registered for Alembic

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="RealtorClaw API",
    description="AI-powered real estate platform with voice-controlled operations, property management, direct mail automation, and intelligent analytics",
    version="1.0.0",
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title, version=app.version,
        description=app.description, routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "x-api-key"}
    }
    openapi_schema["security"] = [{"ApiKeyAuth": []}]
    openapi_schema["tags"] = [
        {"name": "Core", "description": "Agents, properties, contacts, and core entities"},
        {"name": "Video", "description": "Video generation, rendering, and management"},
        {"name": "Marketing", "description": "Campaigns, social media, direct mail"},
        {"name": "Analytics", "description": "Dashboard, alerts, and intelligence"},
        {"name": "Voice", "description": "Voice calls, campaigns, and assistants"},
        {"name": "Deals", "description": "Offers, transactions, and deal management"},
        {"name": "Research", "description": "Property research and market analysis"},
        {"name": "Workflows", "description": "Scheduling, follow-ups, and automation"},
        {"name": "Pipeline", "description": "Activities, deal types, and property pipeline"},
        {"name": "Properties", "description": "Extended property features — comps, websites, photos"},
        {"name": "Operations", "description": "Bulk operations, approvals, and email triage"},
        {"name": "Compliance", "description": "Compliance checks and knowledge base"},
        {"name": "Platform", "description": "System configuration, integrations, and tools"},
    ]
    app.openapi_schema = openapi_schema
    return openapi_schema


app.openapi = custom_openapi

# ---------------------------------------------------------------------------
# Error handlers (must be registered before middleware)
# ---------------------------------------------------------------------------

register_error_handlers(app)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

CORS_ORIGINS = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RateLimitToggleMiddleware)
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(RequestIdMiddleware)
if PROMETHEUS_AVAILABLE:
    app.add_middleware(MetricsMiddleware)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

register_routers(app)

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

app.add_route("/metrics", metrics_endpoint, methods=["GET"])

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

_video_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "videos"))
os.makedirs(_video_dir, exist_ok=True)
app.mount("/videos", StaticFiles(directory=_video_dir), name="videos")

_uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(_uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")

# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, api_key: str = Query(default=None)):
    if not api_key:
        await websocket.close(code=4001, reason="Missing api_key query parameter")
        return
    db = SessionLocal()
    try:
        agent = verify_api_key(db, api_key)
        if not agent:
            await websocket.close(code=4003, reason="Invalid API key")
            return
    finally:
        db.close()

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug("WS message from agent %s: %s", agent.id, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/display/command")
async def send_display_command(command: dict):
    await manager.broadcast(command)
    return {"status": "command_sent", "command": command}

# ---------------------------------------------------------------------------
# Health / Info
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "RealtorClaw API - AI-Powered Real Estate Platform",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    from sqlalchemy import text
    db_status, db_error = "healthy", None
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status, db_error = "unhealthy", str(e)
    finally:
        db.close()

    database_url = os.getenv("DATABASE_URL", "")
    response = {
        "status": db_status,
        "version": "1.0.0",
        "database": {
            "type": "SQLite" if database_url.startswith("sqlite://") else "PostgreSQL",
            "status": db_status,
            "error": db_error,
        },
    }
    # Add circuit breaker status
    try:
        from app.utils.circuit_breaker import circuit_breakers
        response["circuit_breakers"] = circuit_breakers.status()
    except Exception:
        pass

    if db_status != "healthy":
        return JSONResponse(status_code=503, content=response)
    return response


@app.get("/rate-limit")
def rate_limit_status():
    return {
        "rate_limiting": {"enabled": RATE_LIMIT_ENABLED},
        "limits": {"default": RATE_LIMIT_DEFAULT, "burst": "30/minute"},
        "tiers": RATE_LIMIT_TIERS,
    }

# ---------------------------------------------------------------------------
# Cache endpoints
# ---------------------------------------------------------------------------

@app.get("/cache/stats")
async def cache_stats():
    from app.services.cache import google_places_cache, zillow_cache, docuseal_cache
    from app.services.redis_cache import cache_stats as redis_cache_stats
    return {
        "google_places": google_places_cache.stats(),
        "zillow": zillow_cache.stats(),
        "docuseal": docuseal_cache.stats(),
        "redis": await redis_cache_stats(),
    }


@app.post("/cache/clear")
def cache_clear():
    from app.services.cache import google_places_cache, zillow_cache, docuseal_cache
    google_places_cache.clear()
    zillow_cache.clear()
    docuseal_cache.clear()
    return {"message": "All caches cleared"}

# ---------------------------------------------------------------------------
# Background task management (legacy — kept for in-process fallback)
# ---------------------------------------------------------------------------

_background_tasks: list[asyncio.Task] = []


def _prune_done_tasks() -> None:
    """Remove completed tasks from the list to prevent memory leak."""
    _background_tasks[:] = [t for t in _background_tasks if not t.done()]


def add_background_task(task: asyncio.Task) -> None:
    _prune_done_tasks()
    _background_tasks.append(task)


def get_background_tasks() -> list[asyncio.Task]:
    _prune_done_tasks()
    return _background_tasks.copy()

# ---------------------------------------------------------------------------
# Startup / Shutdown
# ---------------------------------------------------------------------------

_bg_started = False


async def _periodic_cache_cleanup():
    while True:
        await asyncio.sleep(3600)
        from app.services.cache import google_places_cache, zillow_cache, docuseal_cache
        google_places_cache.cleanup_expired()
        zillow_cache.cleanup_expired()
        docuseal_cache.cleanup_expired()


@app.on_event("startup")
async def startup_event():
    global _bg_started
    if not _bg_started:
        # Cache cleanup runs in-process (lightweight)
        add_background_task(asyncio.create_task(_periodic_cache_cleanup()))

        # Start in-process task runner as fallback (arq worker handles this when running)
        try:
            from app.job_queue import get_pool
            pool = await get_pool()
            if pool is None:
                # No Redis — fall back to in-process task loop
                from app.services.task_runner import run_task_loop
                add_background_task(asyncio.create_task(run_task_loop()))
                logger.info("No Redis — using in-process task runner")
            else:
                logger.info("Redis available — background jobs handled by arq worker")
        except Exception:
            from app.services.task_runner import run_task_loop
            add_background_task(asyncio.create_task(run_task_loop()))

        _bg_started = True

    logger.info("RealtorClaw Platform ready")


@app.on_event("shutdown")
async def shutdown_event():
    from app.services.cron_scheduler import cron_scheduler
    from app.services.hybrid_search import hybrid_search
    cron_scheduler.stop()
    hybrid_search.close()
    logger.info("RealtorClaw Platform shutdown complete")
