import hashlib
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.portal_cache import PortalCache
from app.services.agentic.utils import utcnow


class SearchProvider(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 5,
        include_text: bool = False,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError


class StubSearchProvider(SearchProvider):
    async def search(
        self,
        query: str,
        max_results: int = 5,
        include_text: bool = False,
    ) -> list[dict[str, Any]]:
        return []


class ExaSearchProvider(SearchProvider):
    """
    Exa search implementation.

    API reference:
    POST {base_url}/search
    headers: x-api-key
    body: {query, type, numResults}
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.exa.ai",
        search_type: str = "auto",
        timeout_seconds: int = 20,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.search_type = search_type
        self.timeout_seconds = timeout_seconds

    async def search(
        self,
        query: str,
        max_results: int = 5,
        include_text: bool = False,
    ) -> list[dict[str, Any]]:
        if not self.api_key:
            return []

        payload = {
            "query": query,
            "type": self.search_type,
            "numResults": max_results,
        }
        if include_text:
            payload["contents"] = {"text": True}

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    headers=headers,
                    json=payload,
                    timeout=float(self.timeout_seconds),
                )
                response.raise_for_status()
                data = response.json()
        except Exception:
            # Fail closed and allow workers to continue with unknowns.
            return []

        normalized: list[dict[str, Any]] = []
        for result in data.get("results", []):
            url = result.get("url")
            if not url:
                continue
            snippet = result.get("text") or ""
            if not snippet and isinstance(result.get("highlights"), list):
                snippet = " ".join(str(item) for item in result.get("highlights")[:2])

            normalized.append(
                {
                    "title": result.get("title") or url,
                    "url": url,
                    "snippet": snippet[:800],
                    "published_date": result.get("publishedDate"),
                    "text": (result.get("text") or "")[:25000] if include_text else "",
                }
            )

        return normalized


def build_search_provider_from_settings() -> SearchProvider:
    if settings.exa_api_key:
        return ExaSearchProvider(
            api_key=settings.exa_api_key,
            base_url=settings.exa_base_url,
            search_type=settings.exa_search_type,
            timeout_seconds=settings.exa_timeout_seconds,
        )
    return StubSearchProvider()


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
        from bs4 import BeautifulSoup  # Lazy import to avoid hard dependency for search-only flows.

        html = await self.fetch_html(db=db, url=url, timeout_seconds=timeout_seconds)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(" ", strip=True)


# Hook for future JS-heavy portal support with Playwright.
async def fetch_with_playwright(url: str) -> str:
    raise NotImplementedError("Playwright scraping hook not implemented yet")
