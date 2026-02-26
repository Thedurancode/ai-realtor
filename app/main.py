from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from typing import List
import asyncio
import json
import os

from app.database import engine, Base, SessionLocal
from app.config import settings
from app.rate_limit import limiter
from app.auth import verify_api_key

# Import phone models FIRST to avoid circular dependency
from app.models.phone_number import PhoneNumber
from app.models.phone_call import PhoneCall

from app.routers import agents_router, properties_router, address_router, skip_trace_router, contacts_router, todos_router, contracts_router, contract_templates_router, agent_preferences_router, context_router, notifications_router, compliance_knowledge_router, compliance_router, activities_router, property_recap_router, webhooks_router, deal_types_router, research_router, research_templates_router, ai_agents_router, elevenlabs_router, agentic_research_router, exa_research_router, voice_campaigns_router, offers_router, search_router, deal_calculator_router, workflows_router, property_notes_router, insights_router, scheduled_tasks_router, analytics_router, pipeline_router, daily_digest_router, follow_ups_router, comps_router, bulk_router, activity_timeline_router, property_scoring_router, market_watchlist_router, web_scraper, approval_router, credential_scrubbing_router, observer_router, agent_brand_router, facebook_ads_router, postiz_router, videogen_router, sqlite_tuning_router, skills_router, setup_router, campaigns_router, document_analysis_router, zuckerbot_router, facebook_targeting_router, renders_router, timeline_router
# Temporarily disabled: voice_assistant
# New intelligence routers
from app.routers import predictive_intelligence, market_opportunities, relationship_intelligence, intelligence
# ZeroClaw-inspired features
from app.routers import workspace, cron_scheduler, hybrid_search
import app.models  # noqa: F401 - ensure all models are registered for Alembic


# Paths that don't require API key authentication
PUBLIC_PATHS = frozenset(("/", "/docs", "/redoc", "/openapi.json", "/health", "/setup"))
PUBLIC_PREFIXES = ("/webhooks/", "/ws", "/cache/", "/agents/register", "/api/setup")


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

from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Real Estate API",
    description="API for real estate agents to manage properties (voice-optimized)",
    version="1.0.0",
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "x-api-key",
        }
    }
    openapi_schema["security"] = [{"ApiKeyAuth": []}]
    app.openapi_schema = openapi_schema
    return openapi_schema


app.openapi = custom_openapi

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
app.include_router(activity_timeline_router)
app.include_router(property_scoring_router)
app.include_router(market_watchlist_router)

# New intelligence routers
app.include_router(predictive_intelligence.router)
app.include_router(market_opportunities.router)
app.include_router(relationship_intelligence.router)
app.include_router(intelligence.router)
# Web scraper router
app.include_router(web_scraper)

# ZeroClaw-inspired features
app.include_router(workspace.router)
app.include_router(cron_scheduler.router)
app.include_router(hybrid_search.router)
# Onboarding
from app.routers import onboarding
app.include_router(onboarding.router)
# Approval Manager
app.include_router(approval_router)
# Credential Scrubbing
app.include_router(credential_scrubbing_router)
# Observer Pattern
app.include_router(observer_router)
# Agent Branding
app.include_router(agent_brand_router)
# Facebook Ads Management
app.include_router(facebook_ads_router)
# Postiz Social Media Marketing
app.include_router(postiz_router)
# VideoGen AI Avatar Videos
app.include_router(videogen_router)
# SQLite Tuning
app.include_router(sqlite_tuning_router)
# Skills System
app.include_router(skills_router)
# Setup Wizard (no authentication required)
app.include_router(setup_router)
# Voice Assistant (Inbound Calling) - Temporarily disabled
# app.include_router(voice_assistant.router)
# Email/Text Campaigns
app.include_router(campaigns_router)
# Document Analysis AI
app.include_router(document_analysis_router)
# Zuckerbot AI Facebook Ads
app.include_router(zuckerbot_router)
app.include_router(facebook_targeting_router)
# Remotion Video Rendering
app.include_router(renders_router)
# Timeline Video Editor
app.include_router(timeline_router)

# Mount static files for timeline editor
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


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


@app.get("/health")
def health_check():
    """
    Health check endpoint for Docker and monitoring systems.
    Checks database connectivity and returns system status.
    """
    import os
    from sqlalchemy import text

    # Check database connection
    db_status = "healthy"
    db_error = None

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)

    # Get database type
    database_url = os.getenv("DATABASE_URL", "")
    is_sqlite = database_url.startswith("sqlite://")
    db_type = "SQLite" if is_sqlite else "PostgreSQL"

    response = {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "version": "1.0.0",
        "database": {
            "type": db_type,
            "status": db_status,
            "error": db_error
        }
    }

    # Return appropriate status code
    if db_status != "healthy":
        from fastapi import status
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response
        )

    return response


# --- Startup and Shutdown Events ---

@app.on_event("startup")
async def startup_event():
    """Initialize background services on startup."""
    import logging
    from app.models.scheduled_task import ScheduledTask

    logger = logging.getLogger(__name__)
    logger.info("Starting AI Realtor Platform...")

    # Start cron scheduler in background
    from app.services.cron_scheduler import cron_scheduler

    asyncio.create_task(cron_scheduler.start())
    logger.info("Cron scheduler started")

    # Create default scheduled tasks if they don't exist
    db = SessionLocal()
    try:
        from app.services.cron_scheduler import CRON_EXPRESSIONS

        # Heartbeat cycle every 5 minutes
        if not db.query(ScheduledTask).filter_by(name="heartbeat_cycle").first():
            await cron_scheduler.schedule_task(
                name="heartbeat_cycle",
                handler_name="heartbeat_cycle",
                cron_expression=CRON_EXPRESSIONS["every_5_minutes"],
                metadata={"description": "Full autonomous monitoring cycle"}
            )
            logger.info("Scheduled heartbeat_cycle task")

        # Portfolio scan every 5 minutes
        if not db.query(ScheduledTask).filter_by(name="portfolio_scan").first():
            await cron_scheduler.schedule_task(
                name="portfolio_scan",
                handler_name="portfolio_scan",
                cron_expression=CRON_EXPRESSIONS["every_5_minutes"],
                metadata={"description": "Scan portfolio for stale properties"}
            )
            logger.info("Scheduled portfolio_scan task")

        # Market intelligence every 15 minutes
        if not db.query(ScheduledTask).filter_by(name="market_intelligence").first():
            await cron_scheduler.schedule_task(
                name="market_intelligence",
                handler_name="market_intelligence",
                cron_expression=CRON_EXPRESSIONS["every_15_minutes"],
                metadata={"description": "Gather market intelligence"}
            )
            logger.info("Scheduled market_intelligence task")

        # Relationship health every hour
        if not db.query(ScheduledTask).filter_by(name="relationship_health").first():
            await cron_scheduler.schedule_task(
                name="relationship_health",
                handler_name="relationship_health",
                cron_expression=CRON_EXPRESSIONS["every_hour"],
                metadata={"description": "Score relationship health"}
            )
            logger.info("Scheduled relationship_health task")

        # Predictive insights every hour
        if not db.query(ScheduledTask).filter_by(name="predictive_insights").first():
            await cron_scheduler.schedule_task(
                name="predictive_insights",
                handler_name="predictive_insights",
                cron_expression=CRON_EXPRESSIONS["every_hour"],
                metadata={"description": "Generate predictive insights"}
            )
            logger.info("Scheduled predictive_insights task")

        db.commit()

    except Exception as e:
        logger.error(f"Error creating default scheduled tasks: {e}")
        db.rollback()
    finally:
        db.close()

    logger.info("AI Realtor Platform startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    import logging

    logger = logging.getLogger(__name__)
    logger.info("Shutting down AI Realtor Platform...")

    # Stop cron scheduler
    from app.services.cron_scheduler import cron_scheduler

    cron_scheduler.stop()
    logger.info("Cron scheduler stopped")

    # Close hybrid search connection
    from app.services.hybrid_search import hybrid_search

    hybrid_search.close()
    logger.info("Hybrid search closed")

    logger.info("AI Realtor Platform shutdown complete")


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
