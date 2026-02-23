"""Web Scraper Service — automated property data extraction from websites."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Optional, List
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from sqlalchemy.orm import Session

from app.models.property import Property, PropertyType
from app.services.google_places import google_places_service
from app.services.zillow_enrichment import zillow_enrichment_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


@dataclass
class ScrapedPropertyData:
    """Structured property data from web scraping."""
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    raw_data: dict = field(default_factory=dict)
    photos: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def is_valid(self) -> bool:
        """Check if scraped data has minimum required fields."""
        return bool(self.address and self.city and self.price)


class WebScraperService:
    """Automated web scraping service for property data extraction."""

    def __init__(self):
        self.timeout = 30.0
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {"User-Agent": self.user_agent}
            self._client = httpx.AsyncClient(
                headers=headers, timeout=self.timeout
            )
        return self._client

    async def scrape_url(
        self,
        url: str,
        use_ai: bool = True,
        source: Optional[str] = None,
    ) -> ScrapedPropertyData:
        """Scrape a single URL and extract property data.

        Args:
            url: URL to scrape
            use_ai: Whether to use AI to extract structured data
            source: Source identifier (zillow, redfin, etc.)

        Returns:
            ScrapedPropertyData with extracted information
        """
        client = await self._get_client()

        try:
            # Fetch the page
            response = await client.get(url)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Detect source and use appropriate scraper
            detected_source = source or self._detect_source(url, soup)

            if detected_source == "zillow":
                scraper = ZillowScraper()
            elif detected_source == "redfin":
                scraper = RedfinScraper()
            elif detected_source == "realtor":
                scraper = RealtorComScraper()
            else:
                scraper = GenericScraper()

            # Scrape the data
            if detected_source == "zillow" and "search" in url.lower():
                # Zillow search results page
                # This returns multiple properties, so handle differently
                results = await ZillowSearchScraper.scrape_search_results(url)
                return results[0] if results else ScrapedPropertyData(url=url)
            else:
                property_data = await scraper.scrape(soup, url)

            # Use AI to extract/clean data if requested
            if use_ai and property_data.raw_data:
                property_data = await self._ai_enrich_extraction(property_data, url)

            property_data.source = detected_source
            return property_data

        except httpx.HTTPError as e:
            logger.error(f"HTTP error scraping {url}: {e}")
            return ScrapedPropertyData(url=url, raw_data={"error": str(e)})
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return ScrapedPropertyData(url=url, raw_data={"error": str(e)})

    async def scrape_multiple_urls(
        self,
        urls: List[str],
        use_ai: bool = True,
        concurrent: int = 3,
    ) -> List[ScrapedPropertyData]:
        """Scrape multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape
            use_ai: Whether to use AI for extraction
            concurrent: Number of concurrent requests

        Returns:
            List of ScrapedPropertyData
        """
        # Limit concurrent requests to avoid overwhelming servers
        semaphore = asyncio.Semaphore(concurrent)

        async def scrape_with_semaphore(url: str) -> ScrapedPropertyData:
            async with semaphore:
                await asyncio.sleep(1)  # Be polite
                return await self.scrape_url(url, use_ai=use_ai)

        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = [
            r for r in results
            if isinstance(r, ScrapedPropertyData) and not r.raw_data.get("error")
        ]

        return valid_results

    async def scrape_and_create_property(
        self,
        db: Session,
        url: str,
        agent_id: int,
        use_ai: bool = True,
        auto_enrich: bool = False,
    ) -> dict[str, Any]:
        """Scrape URL and create property in database.

        Args:
            db: Database session
            url: URL to scrape
            agent_id: Agent to assign property to
            use_ai: Whether to use AI for extraction
            auto_enrich: Whether to auto-enrich with Zillow data

        Returns:
            Created property data
        """
        # Scrape the URL
        scraped_data = await self.scrape_url(url, use_ai=use_ai)

        if not scraped_data.is_valid():
            return {
                "error": f"Invalid scraped data: missing address ({scraped_data.address}), city ({scraped_data.city}), or price ({scraped_data.price})"
            }

        # Check if property already exists
        existing = (
            db.query(Property)
            .filter(
                Property.address == scraped_data.address,
                Property.city == scraped_data.city,
            )
            .first()
        )

        if existing:
            return {
                "error": f"Property already exists: {existing.address}, {existing.city}",
                "existing_property_id": existing.id,
            }

        # Create the property
        try:
            property_type = None
            if scraped_data.property_type:
                property_type = self._map_property_type(scraped_data.property_type)

            prop = Property(
                title=scraped_data.address or f"Property in {scraped_data.city}",
                address=scraped_data.address,
                city=scraped_data.city,
                state=scraped_data.state,
                zip_code=scraped_data.zip_code,
                price=scraped_data.price,
                bedrooms=scraped_data.bedrooms,
                bathrooms=scraped_data.bathrooms,
                square_feet=scraped_data.square_feet,
                lot_size=scraped_data.lot_size,
                year_built=scraped_data.year_built,
                property_type=property_type,
                description=scraped_data.description,
                agent_id=agent_id,
            )

            db.add(prop)
            db.commit()
            db.refresh(prop)

            # Auto-enrich if requested
            if auto_enrich:
                try:
                    await zillow_enrichment_service.enrich_property(
                        db, prop.id, force=True
                    )
                except Exception as e:
                    logger.warning(f"Failed to auto-enrich property {prop.id}: {e}")

            return {
                "property_id": prop.id,
                "address": prop.address,
                "city": prop.city,
                "price": prop.price,
                "message": "Property created successfully",
                "auto_enriched": auto_enrich,
            }

        except Exception as e:
            db.rollback()
            return {
                "error": f"Failed to create property: {str(e)}"
            }

    def _detect_source(self, url: str, soup: BeautifulSoup) -> str:
        """Detect the source/website type from URL and HTML."""
        domain = urlparse(url).netloc.lower()

        if "zillow" in domain:
            return "zillow"
        elif "redfin" in domain:
            return "redfin"
        elif "realtor.com" in domain:
            return "realtor"
        else:
            # Check for meta tags in HTML
            if soup.find("meta", {"property": "og:site_name"}):
                site_name = soup.find("meta", {"property": "og:site_name"}).get("content", "").lower()
                if "zillow" in site_name:
                    return "zillow"
                elif "redfin" in site_name:
                    return "redfin"
                elif "realtor" in site_name:
                    return "realtor"

            return "generic"

    async def _ai_enrich_extraction(
        self,
        scraped_data: ScrapedPropertyData,
        url: str,
    ) -> ScrapedPropertyData:
        """Use AI to extract/clean property data from raw HTML.

        Falls back to Claude Sonnet 4 for intelligent extraction.
        """
        if not scraped_data.raw_data:
            # If no raw data, use the URL to guess what we need
            scraped_data.raw_data = {"url": url}

        prompt = f"""Extract property information from this website data.

URL: {url}

Available Data:
{json.dumps(scraped_data.raw_data, indent=2)}

Extract and return ONLY a JSON object with:
{{
    "address": "full street address",
    "city": "city name",
    "state": "state abbreviation",
    "zip_code": "5-digit ZIP",
    "price": price as number (no $, commas),
    "bedrooms": number of bedrooms or null,
    "bathrooms": number of bathrooms or null,
    "square_feet": total square feet as number or null,
    "year_built": year built as number or null,
    "property_type": "house, condo, townhouse, apartment, land, commercial",
    "description": "property description from the page"
}}

Use the available data above. If a field is not available or cannot be determined, set it to null.
Return ONLY the JSON, no other text."""

        try:
            response = await llm_service.agenerate(prompt, max_tokens=1000)
            import json

            # Extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                extracted = json.loads(json_str)

                # Update scraped data with AI-extracted values
                if extracted.get("address"):
                    scraped_data.address = extracted["address"]
                if extracted.get("city"):
                    scraped_data.city = extracted["city"]
                if extracted.get("state"):
                    scraped_data.state = extracted["state"]
                if extracted.get("zip_code"):
                    scraped_data.zip_code = extracted["zip_code"]
                if extracted.get("price"):
                    scraped_data.price = float(extracted["price"]) if extracted["price"] else None
                if extracted.get("bedrooms"):
                    scraped_data.bedrooms = int(extracted["bedrooms"])
                if extracted.get("bathrooms"):
                    scraped_data.bathrooms = float(extracted["bathrooms"])
                if extracted.get("square_feet"):
                    scraped_data.square_feet = int(extracted["square_feet"])
                if extracted.get("year_built"):
                    scraped_data.year_built = int(extracted["year_built"])
                if extracted.get("property_type"):
                    scraped_data.property_type = extracted["property_type"]
                if extracted.get("description"):
                    scraped_data.description = extracted["description"]

            else:
                logger.warning("AI extraction failed to return JSON")

        except Exception as e:
            logger.error(f"AI enrichment failed: {e}")

        return scraped_data

    def _map_property_type(self, type_str: str) -> Optional[PropertyType]:
        """Map string to PropertyType enum."""
        type_lower = type_str.lower()

        mapping = {
            "house": PropertyType.HOUSE,
            "single family": PropertyType.HOUSE,
            "single family home": PropertyType.HOUSE,
            "condo": PropertyType.CONDO,
            "condominium": PropertyType.CONDO,
            "townhouse": PropertyType.TOWNHOUSE,
            "apartment": PropertyType.APARTMENT,
            "land": PropertyType.LAND,
            "lot": PropertyType.LAND,
            "commercial": PropertyType.COMMERCIAL,
        }

        return mapping.get(type_lower)


class ZillowScraper:
    """Specialized scraper for Zillow listing pages."""

    @staticmethod
    async def scrape_zillow(url: str) -> ScrapedPropertyData:
        """Scrape a Zillow listing page."""
        client = httpx.AsyncClient(timeout=30)
        try:
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            data = ScrapedPropertyData(url=url)

            # Extract address
            address_elem = soup.find("h1", class_="Text-c11n-8-69")
            if address_elem:
                data.address = address_elem.get_text(strip=True)

            # Extract price
            price_elem = soup.find("span", class_="Text-c11n-8-76")
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Extract number from "$123,456" or "$123,456K"
                match = re.search(r"\$?([\d,]+)", price_text.replace(",", ""))
                if match:
                    data.price = float(match.group(1))

            # Extract key facts
            facts = soup.find_all("li", class_="Text-c11n-8-59")
            for fact in facts:
                text = fact.get_text(strip=True)
                if "beds" in text.lower():
                    match = re.search(r"(\d+)", text)
                    if match:
                        data.bedrooms = int(match.group(1))
                elif "baths" in text.lower():
                    match = re.search(r"([\d.]+)", text)
                    if match:
                        data.bathrooms = float(match.group(1))
                elif "sqft" in text.lower():
                    match = re.search(r"([\d,]+)", text.replace(",", ""))
                    if match:
                        data.square_feet = int(match.group(1))
                elif "year built" in text.lower():
                    match = re.search(r"(\d{4})", text)
                    if match:
                        data.year_built = int(match.group(1))

            # Extract city/state from URL or page
            if "/homedetails/" in url:
                # Zillow URL format: /homedetails/12345678_zpid/
                # Often city/state in meta tags
                city_elem = soup.find("meta", {"property": "og:locality"})
                state_elem = soup.find("meta", {"property": "og:region"})
                if city_elem:
                    data.city = city_elem.get("content", "")
                if state_elem:
                    data.state = state_elem.get("content", "")

            # Extract description
            desc_elem = soup.find("meta", {"name": "description"})
            if desc_elem:
                data.description = desc_elem.get("content", "")

            return data

        except Exception as e:
            logger.error(f"Zillow scraper error: {e}")
            return ScrapedPropertyData(url=url)


class RedfinScraper:
    """Specialized scraper for Redfin listing pages."""

    @staticmethod
    async def scrape_redfin(url: str) -> ScrapedPropertyData:
        """Scrape a Redfin listing page."""
        client = httpx.AsyncClient(timeout=30)
        try:
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            data = ScrapedPropertyData(url=url)

            # Redfin uses JSON-LD for structured data
            script = soup.find("script", type="application/ld+json")
            if script:
                try:
                    json_data = json.loads(script.string)

                    if isinstance(json_data, list) and len(json_data) > 0:
                        json_data = json_data[0]

                    if isinstance(json_data, dict):
                        if json_data.get("@type") == "SingleFamilyResidence":
                            data.address = json_data.get("address", {}).get("streetAddress")
                            data.city = json_data.get("address", {}).get("addressLocality")
                            data.state = json_data.get("address", {}).get("addressRegion")
                            data.zip_code = json_data.get("postalCode")
                            data.price = json_data.get("price")
                            data.bedrooms = json_data.get("numberOfRooms")
                            data.square_feet = json_data.get("floorSize", {}).get("value")

                except json.JSONDecodeError:
                    pass

            return data

        except Exception as e:
            logger.error(f"Redfin scraper error: {e}")
            return ScrapedPropertyData(url=url)


class RealtorComScraper:
    """Specialized scraper for Realtor.com listing pages."""

    @staticmethod
    async def scrape_realtor(url: str) -> ScrapedPropertyData:
        """Scrape a Realtor.com listing page."""
        client = httpx.AsyncClient(timeout=30)
        try:
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            data = ScrapedPropertyData(url=url)

            # Extract price
            price_elem = soup.find("span", class_="price")
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                match = re.search(r"\$?([\d,]+)", price_text.replace(",", ""))
                if match:
                    data.price = float(match.group(1))

            # Extract address
            address_elem = soup.find("h1", class_="page-title")
            if address_elem:
                data.address = address_elem.get_text(strip=True)

            # Extract specs
            specs = soup.find_all("li", class_="specs-item")
            for spec in specs:
                text = spec.get_text(strip=True)
                if "bed" in text.lower():
                    match = re.search(r"(\d+)", text)
                    if match:
                        data.bedrooms = int(match.group(1))
                elif "bath" in text.lower():
                    match = re.search(r"([\d.]+)", text)
                    if match:
                        data.bathrooms = float(match.group(1))
                elif "sqft" in text.lower():
                    match = re.search(r"([\d,]+)", text.replace(",", ""))
                    if match:
                        data.square_feet = int(match.group(1))

            return data

        except Exception as e:
            logger.error(f"Realtor.com scraper error: {e}")
            return ScrapedPropertyData(url=url)


class ZillowSearchScraper:
    """Scrape Zillow search results pages to extract multiple properties."""

    @staticmethod
    async def scrape_search_results(url: str, max_properties: int = 20) -> List[ScrapedPropertyData]:
        """Scrape Zillow search results and extract all properties."""
        client = httpx.AsyncClient(timeout=30)
        try:
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            properties = []

            # Find all property cards
            cards = soup.find_all("article", class_="list-card-info")

            for card in cards[:max_properties]:
                data = ScrapedPropertyData()

                # Extract address
                addr_elem = card.find("a", class_="list-card-link")
                if addr_elem:
                    data.address = addr_elem.get_text(strip=True)
                    link = addr_elem.get("href", "")
                    if link:
                        data.url = urljoin("https://www.zillow.com", link)

                # Extract price
                price_elem = card.find("div", class_="list-card-price")
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    match = re.search(r"\$?([\d,]+)", price_text.replace(",", ""))
                    if match:
                        data.price = float(match.group(1))

                # Extract details
                details = card.find_all("li", class_=re.compile("list-card-.*"))
                for detail in details:
                    text = detail.get_text(strip=True)
                    if "bd" in text.lower():
                        match = re.search(r"(\d+)", text)
                        if match:
                            data.bedrooms = int(match.group(1))
                    elif "ba" in text.lower():
                        match = re.search(r"([\d.]+)", text)
                        if match:
                            data.bathrooms = float(match.group(1))
                    elif "sqft" in text.lower():
                        match = re.search(r"([\d,]+)", text.replace(",", ""))
                        if match:
                            data.square_feet = int(match.group(1))

                if data.address:  # Only include if we got an address
                    properties.append(data)

            return properties

        except Exception as e:
            logger.error(f"Zillow search scraper error: {e}")
            return []


class GenericScraper:
    """Generic web scraper using AI to extract property data."""

    @staticmethod
    async def scrape(soup: BeautifulSoup, url: str) -> ScrapedPropertyData:
        """Generic scraper using AI to extract data."""
        # Get page text
        text = soup.get_text(separator=" ", strip=True)

        data = ScrapedPropertyData(
            url=url,
            raw_data={"page_text": text[:5000]}  # First 5000 chars
        )

        return data


web_scraper_service = WebScraperService()
