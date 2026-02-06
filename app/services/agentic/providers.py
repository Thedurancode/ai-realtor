import hashlib
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.portal_cache import PortalCache
from app.services.agentic.utils import utcnow


class SearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError


class StubSearchProvider(SearchProvider):
    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        return []


class PortalCacheService:
    def __init__(self, ttl_hours: int = 24):
        self.ttl_hours = ttl_hours

    def _url_hash(self, url: str) -> str:
        return hashlib.sha256(url.strip().lower().encode("utf-8")).hexdigest()

    def get(self, db: Session, url: str) -> str | None:
        record = (
            db.query(PortalCache)
            .filter(PortalCache.url_hash == self._url_hash(url))
            .first()
        )
        if not record:
            return None

        if record.expires_at <= utcnow():
            return None

        return record.raw_html

    def set(self, db: Session, url: str, raw_html: str) -> None:
        url_hash = self._url_hash(url)
        expires_at = utcnow() + timedelta(hours=self.ttl_hours)
        existing = db.query(PortalCache).filter(PortalCache.url_hash == url_hash).first()
        if existing:
            existing.source_url = url
            existing.raw_html = raw_html
            existing.captured_at = utcnow()
            existing.expires_at = expires_at
        else:
            db.add(
                PortalCache(
                    url_hash=url_hash,
                    source_url=url,
                    raw_html=raw_html,
                    captured_at=utcnow(),
                    expires_at=expires_at,
                )
            )
        db.commit()


class PortalFetcher:
    def __init__(self, cache_service: PortalCacheService | None = None):
        self.cache_service = cache_service or PortalCacheService()

    async def fetch_html(self, db: Session, url: str, timeout_seconds: int = 20) -> str:
        cached = self.cache_service.get(db, url)
        if cached is not None:
            return cached

        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=float(timeout_seconds))
            response.raise_for_status()
            html = response.text

        self.cache_service.set(db, url, html)
        return html

    async def extract_text(self, db: Session, url: str, timeout_seconds: int = 20) -> str:
        html = await self.fetch_html(db=db, url=url, timeout_seconds=timeout_seconds)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(" ", strip=True)


# Hook for future JS-heavy portal support with Playwright.
async def fetch_with_playwright(url: str) -> str:
    raise NotImplementedError("Playwright scraping hook not implemented yet")
