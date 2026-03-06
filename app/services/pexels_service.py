"""Pexels Service

Searches Pexels for stock video footage to use in Creatomate property videos.
Auto-generates search queries from property data or accepts custom overrides.
"""
import json
import logging
import re
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Feature keywords to scan for in Zillow descriptions / reso_facts
_FEATURE_KEYWORDS = {
    "pool": "luxury swimming pool",
    "swimming": "luxury swimming pool",
    "kitchen": "modern kitchen interior",
    "garage": "home garage exterior",
    "garden": "beautiful home garden",
    "fireplace": "cozy fireplace living room",
    "hardwood": "hardwood floor interior",
    "patio": "outdoor patio living",
    "balcony": "balcony city view",
    "waterfront": "waterfront property view",
    "ocean": "ocean view property",
    "lake": "lakefront property view",
    "mountain": "mountain view landscape",
    "basement": "finished basement interior",
    "solar": "solar panel home",
    "gym": "home gym interior",
    "wine": "wine cellar luxury",
}

# Map PropertyType enum values to search terms
_PROPERTY_TYPE_QUERIES = {
    "HOUSE": "house exterior drone shot",
    "APARTMENT": "modern apartment building",
    "CONDO": "luxury condo interior",
    "TOWNHOUSE": "townhouse neighborhood street",
    "LAND": "vacant land aerial view",
    "COMMERCIAL": "commercial building exterior",
}

_GENERIC_FALLBACKS = [
    "real estate aerial view",
    "luxury home interior",
    "suburban neighborhood drone",
    "modern home walkthrough",
    "residential street aerial",
]


class PexelsService:
    """Service for fetching stock video footage from Pexels."""

    BASE_URL = "https://api.pexels.com"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.pexels_api_key
        if not self.api_key:
            logger.warning("Pexels API key not configured")

    async def search_videos(self, query: str, per_page: int = 1) -> list[dict]:
        """Search Pexels for videos matching a query.

        Returns list of video result dicts from the Pexels API.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/videos/search",
                params={
                    "query": query,
                    "per_page": per_page,
                    "orientation": "landscape",
                },
                headers={"Authorization": self.api_key},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("videos", [])

    @staticmethod
    def _best_video_url(video: dict) -> Optional[str]:
        """Pick the best quality MP4 URL from a Pexels video result."""
        files = video.get("video_files", [])
        # Prefer HD, then largest by width
        hd = [f for f in files if f.get("quality") == "hd" and f.get("file_type") == "video/mp4"]
        if hd:
            # Pick widest
            hd.sort(key=lambda f: f.get("width", 0), reverse=True)
            return hd[0].get("link")
        # Fallback: any mp4
        mp4s = [f for f in files if f.get("file_type") == "video/mp4"]
        if mp4s:
            mp4s.sort(key=lambda f: f.get("width", 0), reverse=True)
            return mp4s[0].get("link")
        return None

    @staticmethod
    def generate_search_queries(property_obj, zillow_enrichment) -> list[str]:
        """Auto-generate up to 5 search queries from property data.

        Args:
            property_obj: Property SQLAlchemy model.
            zillow_enrichment: ZillowEnrichment model (or None).

        Returns:
            List of up to 5 search query strings.
        """
        queries: list[str] = []

        # 1. Property type query
        prop_type = property_obj.property_type
        type_val = prop_type.value if hasattr(prop_type, "value") else str(prop_type)
        type_query = _PROPERTY_TYPE_QUERIES.get(type_val, "house exterior drone shot")
        queries.append(type_query)

        if zillow_enrichment:
            # 2. Scan description for feature keywords
            desc = (zillow_enrichment.description or "").lower()
            for keyword, search_term in _FEATURE_KEYWORDS.items():
                if keyword in desc and search_term not in queries:
                    queries.append(search_term)
                    if len(queries) >= 5:
                        return queries

            # 3. Scan reso_facts for amenity keywords
            reso = zillow_enrichment.reso_facts
            if reso:
                reso_str = json.dumps(reso).lower() if isinstance(reso, dict) else str(reso).lower()
                for keyword, search_term in _FEATURE_KEYWORDS.items():
                    if keyword in reso_str and search_term not in queries:
                        queries.append(search_term)
                        if len(queries) >= 5:
                            return queries

            # 4. Home type from Zillow (may differ from property_type)
            home_type = zillow_enrichment.home_type
            if home_type:
                ht_query = f"{home_type.lower().replace('_', ' ')} real estate"
                if ht_query not in queries:
                    queries.append(ht_query)
                    if len(queries) >= 5:
                        return queries

        # 5. Location context
        city = property_obj.city or ""
        state = property_obj.state or ""
        if city and state:
            location_query = f"{city} {state} neighborhood aerial"
            if location_query not in queries:
                queries.append(location_query)
                if len(queries) >= 5:
                    return queries

        # 6. Fill remaining with generic fallbacks
        for fallback in _GENERIC_FALLBACKS:
            if fallback not in queries:
                queries.append(fallback)
                if len(queries) >= 5:
                    return queries

        return queries[:5]

    async def get_stock_videos(self, queries: list[str]) -> list[str]:
        """Search Pexels for each query and return up to 5 HD video URLs.

        Args:
            queries: List of search query strings.

        Returns:
            List of video URLs (may be fewer than 5 if some searches fail).
        """
        urls: list[str] = []
        for query in queries[:5]:
            try:
                results = await self.search_videos(query, per_page=1)
                if results:
                    url = self._best_video_url(results[0])
                    if url:
                        urls.append(url)
                        continue
                logger.warning(f"No Pexels video found for query: {query}")
            except Exception as e:
                logger.error(f"Pexels search failed for '{query}': {e}")
        return urls
