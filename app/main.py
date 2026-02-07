from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from typing import List
import asyncio
import json

from app.database import engine, Base
from app.config import settings
from app.rate_limit import limiter
from app.routers import agents_router, properties_router, address_router, skip_trace_router, contacts_router, todos_router, contracts_router, contract_templates_router, agent_preferences_router, context_router, notifications_router, compliance_knowledge_router, compliance_router, activities_router, property_recap_router, webhooks_router, deal_types_router, research_router, research_templates_router, ai_agents_router, elevenlabs_router, agentic_research_router, exa_research_router, voice_campaigns_router
import app.models  # noqa: F401 - ensure all models are registered for Alembic

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
    if settings.campaign_worker_enabled:
        from app.services.voice_campaign_service import run_campaign_worker_loop

        asyncio.create_task(
            run_campaign_worker_loop(
                interval_seconds=settings.campaign_worker_interval_seconds,
                max_calls_per_campaign=settings.campaign_worker_max_calls_per_tick,
            )
        )
