"""
Simple in-memory TTL cache for external API responses.
"""
from datetime import datetime, timedelta
from typing import Optional, Any, Dict


class TTLCache:
    """Time-To-Live cache with automatic expiration."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value if not expired, otherwise None."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        if datetime.now() > entry["expires_at"]:
            del self._cache[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: int):
        """Store value with TTL in seconds."""
        self._cache[key] = {
            "value": value,
            "expires_at": datetime.now() + timedelta(seconds=ttl_seconds),
        }

    def delete(self, key: str):
        """Remove a key."""
        self._cache.pop(key, None)

    def clear(self):
        """Clear all entries."""
        self._cache.clear()

    def cleanup_expired(self):
        """Remove expired entries to prevent memory growth."""
        now = datetime.now()
        expired = [k for k, v in self._cache.items() if now > v["expires_at"]]
        for k in expired:
            del self._cache[k]

    def stats(self) -> Dict[str, int]:
        """Return cache statistics."""
        now = datetime.now()
        total = len(self._cache)
        valid = sum(1 for v in self._cache.values() if now <= v["expires_at"])
        return {"total_entries": total, "valid_entries": valid, "expired_entries": total - valid}


# Global cache instances
google_places_cache = TTLCache()
zillow_cache = TTLCache()
docuseal_cache = TTLCache()
