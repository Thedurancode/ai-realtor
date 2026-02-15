from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from typing import List
import asyncio
import json

from app.database import engine, Base, SessionLocal
from app.config import settings
from app.rate_limit import limiter
from app.auth import verify_api_key
from app.routers import agents_router, properties_router, address_router, skip_trace_router, contacts_router, todos_router, contracts_router, contract_templates_router, agent_preferences_router, context_router, notifications_router, compliance_knowledge_router, compliance_router, activities_router, property_recap_router, webhooks_router, deal_types_router, research_router, research_templates_router, ai_agents_router, elevenlabs_router, agentic_research_router, exa_research_router, voice_campaigns_router, offers_router, search_router, deal_calculator_router, workflows_router, property_notes_router, insights_router, scheduled_tasks_router, analytics_router, pipeline_router, daily_digest_router, follow_ups_router, comps_router, bulk_router
import app.models  # noqa: F401 - ensure all models are registered for Alembic


# Paths that don't require API key authentication
PUBLIC_PATHS = frozenset(("/", "/docs", "/redoc", "/openapi.json"))
PUBLIC_PREFIXES = ("/webhooks/", "/ws", "/cache/")


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Validate X-API-Key header on all non-public requests."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip auth for public paths
        if path in PUBLIC_PATHS or any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        api_key = request.headers.get("x-api-key")
        if not api_key:
            return JSONResponse(status_code=401, content={"detail": "Missing API key"})

        db = SessionLocal()
        try:
            agent = verify_api_key(db, api_key)
            if not agent:
                return JSONResponse(status_code=401, content={"detail": "Invalid API key"})
            request.state.agent_id = agent.id
        finally:
            db.close()

        return await call_next(request)

app = FastAPI(
    title="Real Estate API",
    description="API for real estate agents to manage properties (voice-optimized)",
    version="1.0.0",
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3025", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key authentication middleware
app.add_middleware(ApiKeyMiddleware)

app.include_router(agents_router)
app.include_router(properties_router)
app.include_router(address_router)
app.include_router(skip_trace_router)
app.include_router(contacts_router)
app.include_router(todos_router)
app.include_router(contracts_router)
app.include_router(contract_templates_router)
app.include_router(agent_preferences_router)
app.include_router(context_router)
app.include_router(notifications_router)
app.include_router(compliance_knowledge_router)
app.include_router(compliance_router)
app.include_router(activities_router)
app.include_router(property_recap_router)
app.include_router(webhooks_router)
app.include_router(deal_types_router)
app.include_router(research_router)
app.include_router(research_templates_router)
app.include_router(ai_agents_router)
app.include_router(elevenlabs_router)
app.include_router(agentic_research_router)
app.include_router(exa_research_router)
app.include_router(voice_campaigns_router)
app.include_router(offers_router)
app.include_router(search_router)
app.include_router(deal_calculator_router)
app.include_router(workflows_router)
app.include_router(property_notes_router)
app.include_router(insights_router)
app.include_router(scheduled_tasks_router)
app.include_router(analytics_router)
app.include_router(pipeline_router)
app.include_router(daily_digest_router)
app.include_router(follow_ups_router)
app.include_router(comps_router)
app.include_router(bulk_router)


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to connection: {e}")


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive any messages
            data = await websocket.receive_text()
            print(f"Received from client: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")


@app.post("/display/command")
async def send_display_command(command: dict):
    """
    Send a command to the TV display via WebSocket

    Example commands:
    - {"action": "show_property", "property_id": 3}
    - {"action": "show_property", "address": "broadway"}
    - {"action": "agent_speak", "message": "Let me show you this property"}
    - {"action": "close_detail"}
    """
    await manager.broadcast(command)
    return {"status": "command_sent", "command": command}


@app.get("/")
def root():
    return {"message": "Real Estate API", "docs": "/docs"}


# --- Cache management endpoints ---

@app.get("/cache/stats")
def cache_stats():
    """Get cache statistics for monitoring."""
    from app.services.cache import google_places_cache, zillow_cache, docuseal_cache
    return {
        "google_places": google_places_cache.stats(),
        "zillow": zillow_cache.stats(),
        "docuseal": docuseal_cache.stats(),
    }


@app.post("/cache/clear")
def cache_clear():
    """Clear all caches."""
    from app.services.cache import google_places_cache, zillow_cache, docuseal_cache
    google_places_cache.clear()
    zillow_cache.clear()
    docuseal_cache.clear()
    return {"message": "All caches cleared"}


# --- Periodic cache cleanup ---

async def _periodic_cache_cleanup():
    """Clean expired cache entries every hour."""
    while True:
        await asyncio.sleep(3600)
        from app.services.cache import google_places_cache, zillow_cache, docuseal_cache
        google_places_cache.cleanup_expired()
        zillow_cache.cleanup_expired()
        docuseal_cache.cleanup_expired()


@app.on_event("startup")
async def startup():
    asyncio.create_task(_periodic_cache_cleanup())

    # Scheduled task runner (reminders, recurring tasks)
    from app.services.task_runner import run_task_loop
    asyncio.create_task(run_task_loop())

    if settings.campaign_worker_enabled:
        from app.services.voice_campaign_service import run_campaign_worker_loop

        asyncio.create_task(
            run_campaign_worker_loop(
                interval_seconds=settings.campaign_worker_interval_seconds,
                max_calls_per_campaign=settings.campaign_worker_max_calls_per_tick,
            )
        )

    # Auto-schedule daily digest if enabled
    if settings.daily_digest_enabled:
        _schedule_daily_digest()


def _schedule_daily_digest():
    """Ensure a recurring daily digest task exists."""
    try:
        from app.models.scheduled_task import ScheduledTask, TaskType, TaskStatus
        from datetime import datetime, timezone, timedelta

        db = SessionLocal()
        try:
            existing = (
                db.query(ScheduledTask)
                .filter(
                    ScheduledTask.task_type == TaskType.RECURRING,
                    ScheduledTask.action == "generate_daily_digest",
                    ScheduledTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING]),
                )
                .first()
            )
            if existing:
                return  # Already scheduled

            # Schedule for next occurrence at configured hour
            now = datetime.now(timezone.utc)
            next_run = now.replace(hour=settings.daily_digest_hour, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)

            task = ScheduledTask(
                task_type=TaskType.RECURRING,
                status=TaskStatus.PENDING,
                title="Daily Digest",
                description="AI-generated morning briefing with portfolio insights and alerts",
                scheduled_at=next_run,
                repeat_interval_hours=24,
                next_run_at=next_run,
                action="generate_daily_digest",
                created_by="system",
            )
            db.add(task)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Failed to schedule daily digest: %s", e)
