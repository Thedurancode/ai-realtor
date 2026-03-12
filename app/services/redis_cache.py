"""Redis-backed response cache for high-traffic endpoints.

Uses the same Redis instance as the arq job queue.
Falls back gracefully when Redis is unavailable.
"""
import hashlib
import json
import logging
import os
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

_redis_client = None
_redis_available: Optional[bool] = None


def _get_redis():
    """Lazy-init Redis client, reusing arq settings."""
    global _redis_client, _redis_available
    if _redis_available is False:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", 6379))
        db = int(os.getenv("REDIS_DB", 0))
        _redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True, socket_timeout=2)
        _redis_client.ping()
        _redis_available = True
        logger.info("Redis cache connected")
        return _redis_client
    except Exception as e:
        _redis_available = False
        logger.warning("Redis cache unavailable: %s — caching disabled", e)
        return None


def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a deterministic cache key."""
    raw = f"{prefix}:{json.dumps(args, default=str)}:{json.dumps(kwargs, sort_keys=True, default=str)}"
    return f"rc:{hashlib.md5(raw.encode()).hexdigest()}"


async def cache_get(key: str) -> Optional[Any]:
    """Get a value from Redis cache."""
    r = _get_redis()
    if r is None:
        return None
    try:
        val = r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set a value in Redis cache with TTL in seconds."""
    r = _get_redis()
    if r is None:
        return
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


async def cache_delete(pattern: str) -> None:
    """Delete cache keys matching a pattern."""
    r = _get_redis()
    if r is None:
        return
    try:
        keys = r.keys(f"rc:*{pattern}*")
        if keys:
            r.delete(*keys)
    except Exception:
        pass


async def cache_stats() -> dict:
    """Get cache statistics."""
    r = _get_redis()
    if r is None:
        return {"status": "unavailable"}
    try:
        info = r.info("memory")
        keys = r.dbsize()
        return {
            "status": "connected",
            "keys": keys,
            "used_memory": info.get("used_memory_human", "unknown"),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def cached(prefix: str, ttl: int = 300):
    """Decorator to cache endpoint responses in Redis.

    Usage:
        @cached("property_search", ttl=120)
        async def search_properties(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = cache_key(prefix, *args, **kwargs)
            result = await cache_get(key)
            if result is not None:
                return result
            result = await func(*args, **kwargs)
            await cache_set(key, result, ttl)
            return result
        return wrapper
    return decorator
