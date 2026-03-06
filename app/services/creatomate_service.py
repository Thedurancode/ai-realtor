"""Creatomate Service

Generates branded property showcase videos using Creatomate's render API.
Maps property data (from Zillow enrichment) and agent branding into
Creatomate template modifications, then kicks off an async render.
"""
import logging
from typing import Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class CreatomateService:
    """Service for rendering branded property videos via Creatomate API."""

    BASE_URL = "https://api.creatomate.com/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.creatomate_api_key
        if not self.api_key:
            logger.warning("Creatomate API key not configured")

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    # ------------------------------------------------------------------
    # Template field mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_photos(zillow_enrichment) -> Dict[str, str]:
        """Extract up to 5 photo URLs from Zillow enrichment data."""
        modifications = {}
        photos = []

        if zillow_enrichment:
            raw_photos = zillow_enrichment.photos
            if isinstance(raw_photos, list):
                photos = raw_photos[:5]

        for i, photo_url in enumerate(photos, start=1):
            # Handle both plain URL strings and dict-style photo objects
            url = photo_url if isinstance(photo_url, str) else photo_url.get("url", "")
            if url:
                modifications[f"Photo-{i}.source"] = url

        return modifications

    @staticmethod
    def _extract_stock_videos(stock_video_urls: List[str]) -> Dict[str, str]:
        """Map stock video URLs to Video-1.source through Video-5.source."""
        modifications = {}
        for i, url in enumerate(stock_video_urls[:5], start=1):
            if url:
                modifications[f"Video-{i}.source"] = url
        return modifications

    @staticmethod
    def _build_modifications(
        property_obj, brand, agent_name: str, stock_video_urls: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """Build the full Creatomate modifications dict from property + brand."""
        mods: Dict[str, str] = {}

        # --- Property photos from Zillow enrichment ---
        zillow = getattr(property_obj, "zillow_enrichment", None)
        mods.update(CreatomateService._extract_photos(zillow))

        # --- Address ---
        address_parts = [property_obj.city]
        if property_obj.state:
            address_parts.append(property_obj.state)
        if property_obj.zip_code:
            address_parts[-1] = f"{property_obj.state} {property_obj.zip_code}"
        mods["Address.text"] = ", ".join(address_parts)

        # --- Details line 1: sqft, beds, baths ---
        details_1_parts = []
        if property_obj.square_feet:
            details_1_parts.append(f"{property_obj.square_feet:,} sqft")
        if property_obj.bedrooms is not None:
            details_1_parts.append(f"{property_obj.bedrooms} bed")
        if property_obj.bathrooms is not None:
            bath_val = int(property_obj.bathrooms) if property_obj.bathrooms == int(property_obj.bathrooms) else property_obj.bathrooms
            details_1_parts.append(f"{bath_val} bath")
        mods["Details-1.text"] = " | ".join(details_1_parts) if details_1_parts else ""

        # --- Details line 2: year_built, lot_size/garage, price ---
        details_2_parts = []
        if property_obj.year_built:
            details_2_parts.append(f"Built {property_obj.year_built}")
        if property_obj.lot_size:
            details_2_parts.append(f"{property_obj.lot_size:,.2f} acre lot")
        if property_obj.price is not None:
            details_2_parts.append(f"${property_obj.price:,.0f}")
        mods["Details-2.text"] = " | ".join(details_2_parts) if details_2_parts else ""

        # --- Agent branding ---
        if brand.headshot_url:
            mods["Picture.source"] = brand.headshot_url
        if brand.logo_url:
            mods["Logo-Intro.source"] = brand.logo_url
            mods["Logo-Outro.source"] = brand.logo_url
        if brand.display_email:
            mods["Email.text"] = brand.display_email
        if brand.display_phone:
            mods["Phone-Number.text"] = brand.display_phone
        if brand.company_name:
            mods["Brand-Name.text"] = brand.company_name
        if agent_name:
            mods["Name.text"] = agent_name

        # --- Stock footage videos ---
        if stock_video_urls:
            mods.update(CreatomateService._extract_stock_videos(stock_video_urls))

        return mods

    # ------------------------------------------------------------------
    # API calls
    # ------------------------------------------------------------------

    async def render_property_video(
        self,
        template_id: str,
        property_obj,
        brand,
        agent_name: str,
        stock_video_urls: Optional[List[str]] = None,
    ) -> Dict:
        """
        Start a Creatomate render for a property showcase video.

        Args:
            template_id: Creatomate template ID configured on the brand.
            property_obj: Property SQLAlchemy model (with zillow_enrichment loaded).
            brand: AgentBrand SQLAlchemy model.
            agent_name: Agent's full name.

        Returns:
            List item dict with render id, status, and url (when available).
        """
        modifications = self._build_modifications(property_obj, brand, agent_name, stock_video_urls)

        payload = {
            "template_id": template_id,
            "modifications": modifications,
        }

        logger.info(f"Starting Creatomate render with template {template_id}")
        logger.debug(f"Modifications: {modifications}")

        try:
            resp = await self.client.post("/renders", json=[payload])
            resp.raise_for_status()
            data = resp.json()

            # Creatomate returns a list of renders
            render = data[0] if isinstance(data, list) and data else data
            logger.info(f"Render started: id={render.get('id')}, status={render.get('status')}")
            return render

        except httpx.HTTPStatusError as e:
            logger.error(f"Creatomate render error: {e.response.text}")
            raise RuntimeError(f"Creatomate render failed: {e.response.text}")

    async def get_render_status(self, render_id: str) -> Dict:
        """
        Check the status of a Creatomate render.

        Args:
            render_id: The render ID returned from render_property_video.

        Returns:
            Dict with id, status, url (when complete), and other metadata.
        """
        try:
            resp = await self.client.get(f"/renders/{render_id}")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Creatomate status check error: {e.response.text}")
            raise RuntimeError(f"Failed to check render status: {e.response.text}")

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
