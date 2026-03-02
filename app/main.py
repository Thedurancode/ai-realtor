from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from typing import List, Dict
import asyncio
import json
import os
from functools import lru_cache

from app.database import engine, Base, SessionLocal
from app.config import settings
from app.rate_limit import limiter, RateLimitToggleMiddleware, RATE_LIMIT_ENABLED, RATE_LIMIT_DEFAULT, RATE_LIMIT_TIERS
from app.auth import verify_api_key

# Import phone models FIRST to avoid circular dependency
from app.models.phone_number import PhoneNumber
from app.models.phone_call import PhoneCall

from app.routers import agents_router, properties_router, address_router, skip_trace_router, contacts_router, todos_router, contracts_router, contract_templates_router, agent_preferences_router, context_router, notifications_router, compliance_knowledge_router, compliance_router, activities_router, property_recap_router, webhooks_router, deal_types_router, research_router, research_templates_router, ai_agents_router, elevenlabs_router, agentic_research_router, exa_research_router, voice_campaigns_router, offers_router, search_router, deal_calculator_router, workflows_router, property_notes_router, insights_router, scheduled_tasks_router, analytics_router, pipeline_router, daily_digest_router, follow_ups_router, comps_router, bulk_router, activity_timeline_router, property_scoring_router, market_watchlist_router, web_scraper, approval_router, credential_scrubbing_router, observer_router, agent_brand_router, postiz_router, videogen_router, sqlite_tuning_router, skills_router, setup_router, campaigns_router, document_analysis_router, zuckerbot_router, facebook_targeting_router, composio_router, renders_router, telnyx, photo_orders, direct_mail_router, contact_lists_router, property_websites, enhanced_property_videos, property_comparison_router
# Temporarily disabled facebook_ads_router due to table conflict
# from app.routers import facebook_ads_router
# NEW: Customer Portal and Document Extraction
from app.routers import portal, document_extraction
# Calendar Integration
from app.routers import calendar
# Advanced Analytics Dashboard
from app.routers import analytics_dashboard
# Analytics Alerts
from app.routers import analytics_alerts
# Property Videos with Voiceover
from app.routers import property_videos
# Temporarily disabled: timeline_router (import errors)
# Temporarily disabled: voice_assistant
# New intelligence routers
from app.routers import predictive_intelligence, market_opportunities, relationship_intelligence, intelligence
# ZeroClaw-inspired features
from app.routers import workspace, cron_scheduler, hybrid_search
import app.models  # noqa: F401 - ensure all models are registered for Alembic


# Paths that don't require API key authentication
PUBLIC_PATHS = frozenset(("/", "/docs", "/redoc", "/openapi.json", "/health", "/setup", "/rate-limit"))
PUBLIC_PREFIXES = ("/webhooks/", "/ws", "/cache/", "/agents/register", "/api/setup", "/composio/", "/portal/", "/videos/")


# Background task initialization state
_background_tasks_initialized = False


def _ensure_background_tasks_started():
    """Ensure background tasks (task runner, cache cleanup) are started."""
    global _background_tasks_initialized

    if _background_tasks_initialized:
        return

    try:
        import asyncio

        # Start cache cleanup
        cache_cleanup_task = asyncio.create_task(_periodic_cache_cleanup())
        add_background_task(cache_cleanup_task)
        print("✓ Cache cleanup task started (lazy init)")

        # Start task runner
        from app.services.task_runner import run_task_loop

        task_runner_task = asyncio.create_task(run_task_loop())
        add_background_task(task_runner_task)
        print("✓ Task runner started (lazy init)")

        _background_tasks_initialized = True

    except Exception as e:
        print(f"❌ Error starting background tasks: {e}")
        import traceback
        traceback.print_exc()


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Validate X-API-Key header on all non-public requests with caching."""

    async def dispatch(self, request: Request, call_next):
        # Ensure background tasks are started on first request
        _ensure_background_tasks_started()

        path = request.url.path

        # Skip auth for public paths
        if path in PUBLIC_PATHS or any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        api_key = request.headers.get("x-api-key")
        if not api_key:
            return JSONResponse(status_code=401, content={"detail": "Missing API key"})

        # Check cache first (avoid DB hit on every request)
        from app.auth import hash_api_key
        key_hash = hash_api_key(api_key)
        cached_agent_id = await get_cached_agent_id(key_hash)

        if cached_agent_id:
            request.state.agent_id = cached_agent_id
            return await call_next(request)

        # Cache miss - query database
        db = SessionLocal()
        try:
            agent = verify_api_key(db, api_key)
            if not agent:
                return JSONResponse(status_code=401, content={"detail": "Invalid API key"})

            # Cache the result for future requests
            await cache_agent_id(key_hash, agent.id)
            request.state.agent_id = agent.id
        finally:
            db.close()

        return await call_next(request)

from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="RealtorClaw API",
    description="AI-powered real estate platform with voice-controlled operations, property management, direct mail automation, and intelligent analytics",
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

# Parse CORS origins from environment variable
CORS_ORIGINS = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limit toggle middleware (enables/disables rate limiting globally)
app.add_middleware(RateLimitToggleMiddleware)

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
app.include_router(property_comparison_router)
app.include_router(workflows_router)
app.include_router(property_notes_router)
app.include_router(insights_router)
app.include_router(scheduled_tasks_router)
app.include_router(analytics_router)
app.include_router(analytics_dashboard.router)
app.include_router(analytics_alerts.router)
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
# Facebook Ads Management (temporarily disabled due to table conflict)
# app.include_router(facebook_ads_router)
# Postiz Social Media Marketing
app.include_router(postiz_router)
# VideoGen AI Avatar Videos
app.include_router(videogen_router)
# Enhanced Property Videos (Avatar + Footage + Assembly)
app.include_router(enhanced_property_videos.router)
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
# Composio MCP Integration
app.include_router(composio_router)
# Remotion Video Rendering (temporarily disabled)
app.include_router(renders_router)
# Property Video Generation with ElevenLabs Voiceover
app.include_router(property_videos.router)
# NEW: Photo Ordering System
app.include_router(photo_orders.router)
# NEW: Direct Mail System (Lob.com)
app.include_router(direct_mail_router)
# NEW: Contact Lists System
app.include_router(contact_lists_router)
# NEW: AI Website Builder
from app.routers import property_websites
app.include_router(property_websites.router)
# Timeline Video Editor (temporarily disabled)
# app.include_router(timeline_router)
# NEW: Customer Portal
app.include_router(portal.router)
# NEW: Document AI Extraction
app.include_router(document_extraction.router)
# NEW: Calendar Integration
app.include_router(calendar.router)
# NEW: Telnyx Voice Integration
app.include_router(telnyx.router)

# Mount static files for timeline editor
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount video files directory for generated property videos (in project directory)
video_dir = os.path.join(os.path.dirname(__file__), "..", "videos")
video_dir = os.path.abspath(video_dir)

# Ensure directory exists (eliminates TOCTOU race condition)
os.makedirs(video_dir, exist_ok=True)
app.mount("/videos", StaticFiles(directory=video_dir), name="videos")

# Mount uploads directory for brand assets and other files
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
uploads_dir = os.path.abspath(uploads_dir)
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Safely remove websocket from active connections."""
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            # Already removed or never was in the list
            pass

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to connection: {e}")


manager = ConnectionManager()


# --- Background Task Management ---
# Store task references to prevent garbage collection
_background_tasks: List[asyncio.Task] = []


def add_background_task(task: asyncio.Task) -> None:
    """Add a background task and store its reference."""
    _background_tasks.append(task)


def get_background_tasks() -> List[asyncio.Task]:
    """Get all background tasks."""
    return _background_tasks.copy()


# --- API Key Cache ---
# Simple in-memory cache for API key verification
_api_key_cache: Dict[str, int] = {}  # {api_key_hash: agent_id}
_cache_lock = asyncio.Lock()


async def get_cached_agent_id(api_key_hash: str) -> int | None:
    """Get agent ID from cache."""
    async with _cache_lock:
        return _api_key_cache.get(api_key_hash)


async def cache_agent_id(api_key_hash: str, agent_id: int) -> None:
    """Cache agent ID for API key."""
    async with _cache_lock:
        _api_key_cache[api_key_hash] = agent_id


def invalidate_api_key_cache(api_key_hash: str | None = None) -> None:
    """Invalidate cache entry or clear entire cache."""
    if api_key_hash:
        _api_key_cache.pop(api_key_hash, None)
    else:
        _api_key_cache.clear()


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
    return {
        "message": "RealtorClaw API - AI-Powered Real Estate Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "mcp_tools": 162,
        "features": [
            "Property Management",
            "AI Website Builder",
            "Direct Mail Automation",
            "Voice-Controlled Operations",
            "AI-Powered Analytics",
            "Marketing Hub",
            "Contract Management",
            "Skip Tracing",
            "Calendar Integration"
        ]
    }


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

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)
    finally:
        db.close()

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


@app.get("/rate-limit")
def rate_limit_status():
    """
    Get current rate limiting configuration.

    Returns rate limit status, tiers, and configuration.
    Useful for monitoring and debugging rate limits.
    """
    return {
        "rate_limiting": {
            "enabled": RATE_LIMIT_ENABLED,
            "message": "Rate limiting is ENABLED" if RATE_LIMIT_ENABLED else "Rate limiting is DISABLED",
        },
        "limits": {
            "default": RATE_LIMIT_DEFAULT,
            "burst": "30/minute",
        },
        "tiers": RATE_LIMIT_TIERS,
        "how_to_disable": {
            "description": "Set RATE_LIMIT_ENABLED environment variable to 'false'",
            "example": "export RATE_LIMIT_ENABLED=false",
        },
        "how_to_enable": {
            "description": "Set RATE_LIMIT_ENABLED environment variable to 'true'",
            "example": "export RATE_LIMIT_ENABLED=true",
        },
        "custom_limits": {
            "description": "Set custom limits via environment variables",
            "variables": {
                "RATE_LIMIT_DEFAULT": "Default limit (default: 20/hour)",
                "RATE_LIMIT_BURST": "Short-term burst limit (default: 30/minute)",
                "RATE_LIMIT_FREE": "Free tier limit (default: 20/hour)",
                "RATE_LIMIT_PRO": "Pro tier limit (default: 100/hour)",
                "RATE_LIMIT_ENTERPRISE": "Enterprise tier limit (default: 1000/hour)",
            }
        }
    }


# --- Startup and Shutdown Events ---

@app.on_event("startup")
async def startup_event():
    """
    Initialize all background services on startup.

    Note: Background tasks are now started lazily on first request
    to ensure reliable startup. See _ensure_background_tasks_started().
    """
    import logging

    logger = logging.getLogger(__name__)
    logger.info("✅ RealtorClaw Platform ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    import logging

    logger = logging.getLogger(__name__)
    logger.info("Shutting down RealtorClaw Platform...")

    # Stop cron scheduler
    from app.services.cron_scheduler import cron_scheduler

    cron_scheduler.stop()
    logger.info("Cron scheduler stopped")

    # Close hybrid search connection
    from app.services.hybrid_search import hybrid_search

    hybrid_search.close()
    logger.info("Hybrid search closed")

    logger.info("RealtorClaw Platform shutdown complete")


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
