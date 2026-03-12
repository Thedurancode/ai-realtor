"""API key authentication middleware."""

import logging
import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api_key_cache import get_cached_agent_id, cache_agent_id
from app.auth import verify_api_key, hash_api_key
from app.database import SessionLocal

logger = logging.getLogger(__name__)

# Paths that don't require API key authentication
PUBLIC_PATHS = frozenset(("/", "/docs", "/redoc", "/openapi.json", "/health", "/setup", "/rate-limit", "/metrics"))
PUBLIC_PREFIXES = ("/webhooks/", "/ws", "/cache/", "/agents/register", "/api/setup", "/portal/")


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Validate X-API-Key header on all non-public requests with caching."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip auth for public paths
        if path in PUBLIC_PATHS or any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        # Skip auth for localhost requests only in test mode
        if os.getenv("TESTING") == "1":
            client_host = request.client.host if request.client else None
            if client_host in ("127.0.0.1", "::1", "localhost"):
                request.state.agent_id = 1
                return await call_next(request)

        api_key = request.headers.get("x-api-key")
        if not api_key:
            return JSONResponse(status_code=401, content={"error": "unauthorized", "message": "Missing API key"})

        # Check cache first
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
                return JSONResponse(status_code=401, content={"error": "unauthorized", "message": "Invalid API key"})
            await cache_agent_id(key_hash, agent.id)
            request.state.agent_id = agent.id
        finally:
            db.close()

        return await call_next(request)
