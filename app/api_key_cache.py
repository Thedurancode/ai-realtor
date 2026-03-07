"""In-memory API key verification cache."""

import asyncio
from typing import Dict


_api_key_cache: Dict[str, int] = {}
_cache_lock = asyncio.Lock()


async def get_cached_agent_id(api_key_hash: str) -> int | None:
    async with _cache_lock:
        return _api_key_cache.get(api_key_hash)


async def cache_agent_id(api_key_hash: str, agent_id: int) -> None:
    async with _cache_lock:
        _api_key_cache[api_key_hash] = agent_id


def invalidate_api_key_cache(api_key_hash: str | None = None) -> None:
    if api_key_hash:
        _api_key_cache.pop(api_key_hash, None)
    else:
        _api_key_cache.clear()
