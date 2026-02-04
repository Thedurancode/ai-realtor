"""
Zillow property enrichment service using RapidAPI
"""
import httpx
from typing import Dict, Any, Optional
from app.config import settings


class ZillowEnrichmentService:
    """Enrich property data using Zillow API via RapidAPI"""

    def __init__(self):
        self.api_key = settings.rapidapi_key
        self.api_host = settings.zillow_api_host
        self.base_url = f"https://{self.api_host}"

    async def enrich_by_address(self, address: str) -> Dict[str, Any]:
        """
        Enrich property data by address.

        Args:
            address: Full property address (e.g., "1875 AVONDALE Circle, Jacksonville, FL 32205")

        Returns:
            Dictionary containing enriched property data from Zillow

        Raises:
            httpx.HTTPError: If API request fails
        """
        headers = {
            "x-rapidapi-host": self.api_host,
            "x-rapidapi-key": self.api_key,
        }

        # URL encode the address
        import urllib.parse
        encoded_address = urllib.parse.quote(address)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/pro/byaddress",
                params={"propertyaddress": address},
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        # Parse the response
        return self._parse_zillow_response(data)

    def _parse_zillow_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Zillow API response and extract relevant fields.

        Args:
            data: Raw API response

        Returns:
            Parsed property data
        """
        property_details = data.get("propertyDetails", {})

        # Extract photos
        photos = []
        original_photos = property_details.get("originalPhotos", [])
        for photo in original_photos[:20]:  # Limit to first 20 photos
            if "mixedSources" in photo and "jpeg" in photo["mixedSources"]:
                jpeg_sources = photo["mixedSources"]["jpeg"]
                if jpeg_sources:
                    # Get the highest resolution
                    photos.append(jpeg_sources[-1].get("url"))

        # Extract school information
        schools = []
        for school in property_details.get("schools", [])[:5]:  # Limit to 5 schools
            schools.append({
                "name": school.get("name"),
                "rating": school.get("rating"),
                "distance": school.get("distance"),
                "grades": school.get("grades"),
                "link": school.get("link"),
            })

        # Extract tax history (last 5 years)
        tax_history = []
        for tax in property_details.get("taxHistory", [])[:5]:
            tax_history.append({
                "year": tax.get("time"),
                "tax_paid": tax.get("taxPaid"),
                "value": tax.get("value"),
                "tax_increase_rate": tax.get("taxIncreaseRate"),
            })

        # Extract price history (last 10 events)
        price_history = []
        for price in property_details.get("priceHistory", [])[:10]:
            price_history.append({
                "date": price.get("date"),
                "event": price.get("event"),
                "price": price.get("price"),
                "price_per_sqft": price.get("pricePerSquareFoot"),
                "source": price.get("source"),
            })

        # Extract RESO facts
        reso_facts = property_details.get("resoFacts", {})

        return {
            # Zillow identifiers
            "zpid": property_details.get("zpid"),
            "zillow_url": data.get("zillowURL"),
            "hdp_url": property_details.get("hdpUrl"),

            # Valuation
            "zestimate": property_details.get("zestimate"),
            "zestimate_low_percent": property_details.get("zestimateLowPercent"),
            "zestimate_high_percent": property_details.get("zestimateHighPercent"),
            "rent_zestimate": property_details.get("rentZestimate"),

            # Property details
            "living_area": property_details.get("livingArea"),
            "lot_size": property_details.get("lotSize"),
            "lot_area_value": property_details.get("lotAreaValue"),
            "lot_area_units": property_details.get("lotAreaUnits"),
            "year_built": property_details.get("yearBuilt"),
            "bedrooms": property_details.get("bedrooms"),
            "bathrooms": property_details.get("bathrooms"),
            "home_type": property_details.get("homeType"),
            "home_status": property_details.get("homeStatus"),
            "property_type_dimension": property_details.get("propertyTypeDimension"),

            # Listing information
            "price": property_details.get("price"),
            "days_on_zillow": property_details.get("daysOnZillow"),
            "time_on_zillow": property_details.get("timeOnZillow"),
            "page_view_count": property_details.get("pageViewCount"),
            "favorite_count": property_details.get("favoriteCount"),

            # Tax information
            "property_tax_rate": property_details.get("propertyTaxRate"),
            "annual_tax_amount": reso_facts.get("taxAnnualAmount"),

            # Description
            "description": property_details.get("description"),

            # Media
            "photos": photos,
            "photo_count": property_details.get("photoCount"),

            # Address
            "address": property_details.get("address", {}),
            "latitude": property_details.get("latitude"),
            "longitude": property_details.get("longitude"),

            # Additional data
            "schools": schools,
            "tax_history": tax_history,
            "price_history": price_history,
            "reso_facts": reso_facts,

            # Full raw response
            "raw_response": data,
        }


# Create singleton instance
zillow_enrichment_service = ZillowEnrichmentService()
