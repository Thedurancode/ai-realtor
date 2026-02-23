"""MCP tools for web scraping — voice-controlled property data extraction."""

from mcp_server.tools import register_tool
from mcp_server.utils.context import add_property_context
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.web_scraper_service import web_scraper_service
from typing import Optional


@register_tool({
    "name": "scrape_url",
    "description": "Scrape a property website URL and extract structured data without creating a property. Use this to preview what data would be extracted from a URL. Returns address, price, beds, baths, sqft, and other details.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to scrape (Zillow, Redfin, Realtor.com, or any property website)"
            },
            "use_ai": {
                "type": "boolean",
                "description": "Use AI to enhance data extraction (default: true)",
                "default": True
            }
        },
        "required": ["url"]
    }
})
async def scrape_url_handler(url: str, use_ai: bool = True) -> dict:
    """Scrape a URL and return extracted property data."""
    result = await web_scraper_service.scrape_url(url=url, use_ai=use_ai)

    voice_summary = f"Scraped {result.source or 'website'}"

    if result.address:
        voice_summary += f" for {result.address}"
    if result.city:
        voice_summary += f" in {result.city}"
    if result.price:
        voice_summary += f" priced at ${result.price:,.0f}"

    if not result.is_valid():
        voice_summary += ". Data is incomplete — missing address, city, or price"
    else:
        voice_summary += ". Data looks complete"

    response = {
        "url": url,
        "source": result.source,
        "data": result.to_dict(),
        "is_valid": result.is_valid(),
        "voice_summary": voice_summary
    }

    # Add property context if we found a property_id
    if result.to_dict().get("property_id"):
        add_property_context(result.to_dict()["property_id"], response)

    return response


@register_tool({
    "name": "scrape_and_create",
    "description": "Scrape a property URL and automatically create a new property in the database. Validates data and checks for duplicates. Use this when you want to add a property from a website.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to scrape (Zillow, Redfin, Realtor.com, etc.)"
            },
            "agent_id": {
                "type": "integer",
                "description": "The agent ID to assign the property to"
            },
            "use_ai": {
                "type": "boolean",
                "description": "Use AI to enhance extraction (default: true)",
                "default": True
            },
            "auto_enrich": {
                "type": "boolean",
                "description": "Auto-enrich with Zillow data after creating (default: false)",
                "default": False
            }
        },
        "required": ["url", "agent_id"]
    }
})
async def scrape_and_create_handler(
    url: str,
    agent_id: int,
    use_ai: bool = True,
    auto_enrich: bool = False
) -> dict:
    """Scrape URL and create property."""
    db = SessionLocal()

    try:
        result = await web_scraper_service.scrape_and_create_property(
            db=db,
            url=url,
            agent_id=agent_id,
            use_ai=use_ai,
            auto_enrich=auto_enrich
        )

        if "error" in result:
            return {
                "error": result["error"],
                "voice_summary": f"Failed to create property from URL. {result['error']}"
            }

        voice_summary = f"Created property {result.get('property_id')}"

        if result.get("address"):
            voice_summary += f" at {result['address']}"
        if result.get("city"):
            voice_summary += f" in {result['city']}"
        if result.get("price"):
            voice_summary += f" for ${result['price']:,.0f}"

        if auto_enrich:
            voice_summary += " and enriched with Zillow data"

        voice_summary += "."

        response = {
            **result,
            "voice_summary": voice_summary
        }

        # Add property context
        add_property_context(result["property_id"], response)

        return response

    finally:
        db.close()


@register_tool({
    "name": "scrape_zillow_search",
    "description": "Scrape a Zillow search results page and extract data for multiple properties (up to 20). Returns scraped data without creating properties. Use scrape_and_create_batch to import all of them.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "search_url": {
                "type": "string",
                "description": "The Zillow search results URL (contains /homes/)"
            },
            "max_properties": {
                "type": "integer",
                "description": "Maximum number of properties to extract (default: 20, max: 50)",
                "default": 20
            }
        },
        "required": ["search_url"]
    }
})
async def scrape_zillow_search_handler(search_url: str, max_properties: int = 20) -> dict:
    """Scrape Zillow search results."""
    from app.services.web_scraper_service import ZillowSearchScraper

    results = await ZillowSearchScraper.scrape_search_results(
        url=search_url,
        max_properties=min(max_properties, 50)
    )

    voice_summary = f"Found {len(results)} properties on Zillow"

    if len(results) > 0:
        # Show price range
        prices = [r.price for r in results if r.price]
        if prices:
            voice_summary += f" ranging from ${min(prices):,.0f} to ${max(prices):,.0f}"

    response = {
        "search_url": search_url,
        "properties_found": len(results),
        "properties": [r.to_dict() for r in results],
        "voice_summary": voice_summary
    }

    return response


@register_tool({
    "name": "scrape_and_create_batch",
    "description": "Scrape multiple URLs, create properties from all valid results, and optionally auto-enrich with Zillow data. Best for bulk imports from search results. Handles duplicates, validates data, and returns summary of created properties.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of URLs to scrape (Zillow, Redfin, Realtor.com, etc.)"
            },
            "agent_id": {
                "type": "integer",
                "description": "The agent ID to assign properties to"
            },
            "concurrent": {
                "type": "integer",
                "description": "Number of concurrent requests (default: 3, max: 10)",
                "default": 3
            },
            "auto_enrich": {
                "type": "boolean",
                "description": "Auto-enrich all created properties with Zillow data (default: true)",
                "default": True
            }
        },
        "required": ["urls", "agent_id"]
    }
})
async def scrape_and_create_batch_handler(
    urls: list,
    agent_id: int,
    concurrent: int = 3,
    auto_enrich: bool = True
) -> dict:
    """Batch scrape and create properties."""
    db = SessionLocal()

    try:
        # Import here to avoid circular dependency
        import httpx
        from app.services.zillow_enrichment import zillow_enrichment_service

        # Scrape all URLs
        results = await web_scraper_service.scrape_multiple_urls(
            urls=urls,
            use_ai=True,
            concurrent=min(concurrent, 10)
        )

        created_properties = []
        errors = []

        for scraped_data in results:
            if not scraped_data.is_valid():
                errors.append({
                    "url": scraped_data.url,
                    "error": "Invalid data — missing address, city, or price"
                })
                continue

            # Check for duplicates
            from app.models import Property
            existing = db.query(Property).filter(
                Property.address == scraped_data.address,
                Property.city == scraped_data.city
            ).first()

            if existing:
                errors.append({
                    "url": scraped_data.url,
                    "error": f"Property already exists: ID {existing.id}"
                })
                continue

            # Create property
            try:
                result = await web_scraper_service.scrape_and_create_property(
                    db=db,
                    url=scraped_data.url or "",
                    agent_id=agent_id,
                    use_ai=False,  # Already used AI in scrape_multiple_urls
                    auto_enrich=False  # Will enrich separately below
                )

                if "error" not in result:
                    created_properties.append(result)
                else:
                    errors.append({
                        "url": scraped_data.url,
                        "error": result.get("error", "Unknown error")
                    })

            except Exception as e:
                errors.append({
                    "url": scraped_data.url,
                    "error": str(e)
                })

        # Auto-enrich if requested
        enriched_count = 0
        if auto_enrich and created_properties:
            for prop_result in created_properties:
                prop_id = prop_result.get("property_id")
                if prop_id:
                    try:
                        await zillow_enrichment_service.enrich_property(
                            db, prop_id, force=True
                        )
                        enriched_count += 1
                    except Exception as e:
                        errors.append({
                            "property_id": prop_id,
                            "error": f"Enrichment failed: {str(e)}"
                        })

        voice_summary = f"Processed {len(urls)} URLs"

        if created_properties:
            voice_summary += f", created {len(created_properties)} properties"
            if enriched_count:
                voice_summary += f", and enriched {enriched_count}"

        if errors:
            voice_summary += f", with {len(errors)} errors"

        voice_summary += "."

        response = {
            "total_urls": len(urls),
            "successfully_scraped": len(results),
            "properties_created": len(created_properties),
            "properties_enriched": enriched_count,
            "errors": errors,
            "created_properties": created_properties,
            "voice_summary": voice_summary
        }

        return response

    finally:
        db.close()


@register_tool({
    "name": "scrape_redfin",
    "description": "Scrape a Redfin listing page and create a property. Convenience tool for Redfin URLs.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The Redfin listing URL"
            },
            "agent_id": {
                "type": "integer",
                "description": "The agent ID to assign the property to"
            },
            "auto_enrich": {
                "type": "boolean",
                "description": "Auto-enrich with Zillow data after creating (default: false)",
                "default": False
            }
        },
        "required": ["url", "agent_id"]
    }
})
async def scrape_redfin_handler(url: str, agent_id: int, auto_enrich: bool = False) -> dict:
    """Scrape Redfin URL and create property."""
    db = SessionLocal()

    try:
        result = await web_scraper_service.scrape_and_create_property(
            db=db,
            url=url,
            agent_id=agent_id,
            use_ai=True,
            auto_enrich=auto_enrich
        )

        if "error" in result:
            return {
                "error": result["error"],
                "voice_summary": f"Failed to create property from Redfin. {result['error']}"
            }

        voice_summary = f"Created property from Redfin"

        if result.get("address"):
            voice_summary += f" at {result['address']}"
        if result.get("city"):
            voice_summary += f" in {result['city']}"
        if result.get("price"):
            voice_summary += f" for ${result['price']:,.0f}"

        if auto_enrich:
            voice_summary += " and enriched with Zillow data"

        voice_summary += "."

        response = {
            **result,
            "voice_summary": voice_summary
        }

        # Add property context
        add_property_context(result["property_id"], response)

        return response

    finally:
        db.close()


@register_tool({
    "name": "scrape_realtor",
    "description": "Scrape a Realtor.com listing page and create a property. Convenience tool for Realtor.com URLs.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The Realtor.com listing URL"
            },
            "agent_id": {
                "type": "integer",
                "description": "The agent ID to assign the property to"
            },
            "auto_enrich": {
                "type": "boolean",
                "description": "Auto-enrich with Zillow data after creating (default: false)",
                "default": False
            }
        },
        "required": ["url", "agent_id"]
    }
})
async def scrape_realtor_handler(url: str, agent_id: int, auto_enrich: bool = False) -> dict:
    """Scrape Realtor.com URL and create property."""
    db = SessionLocal()

    try:
        result = await web_scraper_service.scrape_and_create_property(
            db=db,
            url=url,
            agent_id=agent_id,
            use_ai=True,
            auto_enrich=auto_enrich
        )

        if "error" in result:
            return {
                "error": result["error"],
                "voice_summary": f"Failed to create property from Realtor.com. {result['error']}"
            }

        voice_summary = f"Created property from Realtor.com"

        if result.get("address"):
            voice_summary += f" at {result['address']}"
        if result.get("city"):
            voice_summary += f" in {result['city']}"
        if result.get("price"):
            voice_summary += f" for ${result['price']:,.0f}"

        if auto_enrich:
            voice_summary += " and enriched with Zillow data"

        voice_summary += "."

        response = {
            **result,
            "voice_summary": voice_summary
        }

        # Add property context
        add_property_context(result["property_id"], response)

        return response

    finally:
        db.close()
