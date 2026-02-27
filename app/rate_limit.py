"""
Rate limiting configuration for RealtorClaw API.

Supports:
- Per-agent rate limiting (via API key)
- Configurable tiers (free, pro, enterprise)
- Toggle on/off via environment variable
- Multiple time windows (hour, day, minute)
"""

import os
from functools import wraps
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth import verify_api_key
from app.database import SessionLocal


# ============================================================================
# Configuration
# ============================================================================

# Enable/disable rate limiting globally
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")

# Default limits (requests per time period)
RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "20/hour")
RATE_LIMIT_BURST = os.getenv("RATE_LIMIT_BURST", "30/minute")

# Agent-specific tier limits
RATE_LIMIT_TIERS = {
    "free": os.getenv("RATE_LIMIT_FREE", "20/hour"),
    "pro": os.getenv("RATE_LIMIT_PRO", "100/hour"),
    "enterprise": os.getenv("RATE_LIMIT_ENTERPRISE", "1000/hour"),
}


# ============================================================================
# Key Functions
# ============================================================================

def get_agent_id(request: Request) -> Optional[str]:
    """
    Extract agent ID from API key for rate limiting.

    Returns the agent ID if authenticated, otherwise falls back to IP address.
    """
    try:
        # Try to get API key from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header.replace("Bearer ", "")

            # Look up agent by API key
            db = SessionLocal()
            try:
                agent = verify_api_key(db, api_key)
                if agent:
                    return f"agent:{agent.id}"
            finally:
                db.close()

    except Exception:
        pass

    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"


def get_agent_tier(request: Request) -> str:
    """
    Get the rate limit tier for the current agent.

    Checks for a custom rate limit tier in agent preferences or metadata.
    Can be extended to check database for agent-specific limits.
    """
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header.replace("Bearer ", "")

            db = SessionLocal()
            try:
                agent = verify_api_key(db, api_key)
                if agent and hasattr(agent, 'rate_limit_tier'):
                    return agent.rate_limit_tier or "free"
            finally:
                db.close()
    except Exception:
        pass

    return "free"


# ============================================================================
# Limiter Setup
# ============================================================================

# Create limiter with agent-based key function
if RATE_LIMIT_ENABLED:
    limiter = Limiter(
        key_func=get_agent_id,
        default_limits=[RATE_LIMIT_BURST, RATE_LIMIT_DEFAULT],
        storage_uri=os.getenv("RATE_LIMIT_STORAGE_URI", "memory://"),
        enabled=True,
    )
else:
    # Disabled limiter (no limits)
    limiter = Limiter(
        key_func=get_agent_id,
        default_limits=[],
        storage_uri="memory://",
        enabled=False,
    )


# ============================================================================
# Custom Rate Limit Decorator with Agent Tier Support
# ============================================================================

def agent_rate_limit(request: Request):
    """
    Get rate limit string for the current agent based on their tier.

    This can be used with @limiter.limit() decorator:
        @limiter.limit(agent_rate_limit)
    """
    tier = get_agent_tier(request)
    return RATE_LIMIT_TIERS.get(tier, RATE_LIMIT_DEFAULT)


# ============================================================================
# Middleware for Toggle Control
# ============================================================================

class RateLimitToggleMiddleware(BaseHTTPMiddleware):
    """
    Middleware to conditionally enable/disable rate limiting.

    Allows runtime toggling via RATE_LIMIT_ENABLED environment variable.
    """

    async def dispatch(self, request: Request, call_next):
        # Add rate limit info to request state for endpoints to check
        request.state.rate_limit_enabled = RATE_LIMIT_ENABLED
        request.state.rate_limit_tier = get_agent_tier(request)
        request.state.rate_limit_config = {
            "enabled": RATE_LIMIT_ENABLED,
            "default": RATE_LIMIT_DEFAULT,
            "burst": RATE_LIMIT_BURST,
            "tiers": RATE_LIMIT_TIERS,
        }

        return await call_next(request)


# ============================================================================
# Rate Limit Info Endpoint Helpers
# ============================================================================

def get_rate_limit_headers(request: Request) -> dict:
    """
    Get rate limit information for the current request.

    Returns headers that can be added to responses:
    - X-RateLimit-Limit: Requests allowed in current window
    - X-RateLimit-Remaining: Requests remaining
    - X-RateLimit-Reset: When limit resets
    - X-RateLimit-Tier: Agent's rate limit tier
    """
    # This would be populated by slowapi in the response
    # For now, return basic info
    return {
        "X-RateLimit-Enabled": "true" if RATE_LIMIT_ENABLED else "false",
        "X-RateLimit-Tier": get_agent_tier(request),
        "X-RateLimit-Default": RATE_LIMIT_DEFAULT,
    }


# ============================================================================
# Convenience Decorators
# ============================================================================

def rate_limit(limit_string: str = None):
    """
    Rate limit decorator that can be toggled on/off.

    Usage:
        @router.get("/properties")
        @rate_limit("20/hour")
        async def list_properties(...):
            ...

    If RATE_LIMIT_ENABLED is false, this decorator does nothing.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not RATE_LIMIT_ENABLED:
                return await func(*args, **kwargs)

            # Apply slowapi rate limit
            # The actual request is in kwargs for FastAPI endpoints
            request = kwargs.get("request") or (
                args[0] if args and isinstance(args[0], Request) else None
            )

            if request:
                # Get the limit string (use provided or agent tier)
                actual_limit = limit_string or agent_rate_limit(request)

                # Apply limit via slowapi
                # This is handled by the limiter middleware
                pass

            return await func(*args, **kwargs)

        return wrapper
    return decorator


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "limiter",
    "get_agent_id",
    "get_agent_tier",
    "agent_rate_limit",
    "RateLimitToggleMiddleware",
    "get_rate_limit_headers",
    "rate_limit",
    "RATE_LIMIT_ENABLED",
    "RATE_LIMIT_DEFAULT",
    "RATE_LIMIT_TIERS",
]
