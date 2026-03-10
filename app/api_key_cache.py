"""In-memory API key verification cache with TTL."""

import asyncio
import time
from typing import Dict, Tuple

# Cache stores (agent_id, cached_at_timestamp)
_api_key_cache: Dict[str, Tuple[int, float]] = {}
_cache_lock = asyncio.Lock()
CACHE_TTL_SECONDS = 300  # 5 minutes — permission changes take effect within this window


async def get_cached_agent_id(api_key_hash: str) -> int | None:
    async with _cache_lock:
        entry = _api_key_cache.get(api_key_hash)
        if entry is None:
            return None
        agent_id, cached_at = entry
        if time.time() - cached_at > CACHE_TTL_SECONDS:
            del _api_key_cache[api_key_hash]
            return None
        return agent_id


async def cache_agent_id(api_key_hash: str, agent_id: int) -> None:
    async with _cache_lock:
        _api_key_cache[api_key_hash] = (agent_id, time.time())


def invalidate_api_key_cache(api_key_hash: str | None = None) -> None:
    if api_key_hash:
        _api_key_cache.pop(api_key_hash, None)
    else:
        _api_key_cache.clear()
