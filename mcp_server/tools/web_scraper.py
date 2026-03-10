"""MCP tools for web scraping — voice-controlled property data extraction."""

from mcp.types import Tool, TextContent

from ..server import register_tool
from app.database import SessionLocal
from app.services.web_scraper_service import web_scraper_service


async def handle_scrape_url(arguments: dict) -> list[TextContent]:
    """Scrape a property website URL and extract structured data without creating a property."""
    url = arguments.get("url")
    if not url:
        return [TextContent(type="text", text="Please provide a URL to scrape.")]

    use_ai = arguments.get("use_ai", True)
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

    text = f"{voice_summary}\n\nExtracted data:\n"
    data = result.to_dict()
    for key, value in data.items():
        if value is not None:
            text += f"  {key}: {value}\n"

    return [TextContent(type="text", text=text)]


async def handle_scrape_and_create(arguments: dict) -> list[TextContent]:
    """Scrape a property URL and automatically create a new property in the database."""
    url = arguments.get("url")
    agent_id = arguments.get("agent_id")
    if not url or not agent_id:
        return [TextContent(type="text", text="Please provide url and agent_id.")]

    use_ai = arguments.get("use_ai", True)
    auto_enrich = arguments.get("auto_enrich", False)

    db = SessionLocal()
    try:
        result = await web_scraper_service.scrape_and_create_property(
            db=db, url=url, agent_id=agent_id, use_ai=use_ai, auto_enrich=auto_enrich
        )

        if "error" in result:
            return [TextContent(type="text", text=f"Failed to create property from URL. {result['error']}")]

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

        return [TextContent(type="text", text=voice_summary)]
    finally:
        db.close()


async def handle_scrape_zillow_search(arguments: dict) -> list[TextContent]:
    """Scrape a Zillow search results page and extract data for multiple properties."""
    search_url = arguments.get("search_url")
    if not search_url:
        return [TextContent(type="text", text="Please provide a search_url.")]

    max_properties = min(arguments.get("max_properties", 20), 50)

    from app.services.web_scraper_service import ZillowSearchScraper
    results = await ZillowSearchScraper.scrape_search_results(
        url=search_url, max_properties=max_properties
    )

    voice_summary = f"Found {len(results)} properties on Zillow"
    if results:
        prices = [r.price for r in results if r.price]
        if prices:
            voice_summary += f" ranging from ${min(prices):,.0f} to ${max(prices):,.0f}"

    text = voice_summary + "\n\n"
    for i, r in enumerate(results[:20], 1):
        text += f"{i}. {r.address or 'Unknown'}"
        if r.price:
            text += f" — ${r.price:,.0f}"
        text += "\n"

    return [TextContent(type="text", text=text)]


async def handle_scrape_and_create_batch(arguments: dict) -> list[TextContent]:
    """Scrape multiple URLs, create properties from all valid results."""
    urls = arguments.get("urls", [])
    agent_id = arguments.get("agent_id")
    if not urls or not agent_id:
        return [TextContent(type="text", text="Please provide urls and agent_id.")]

    concurrent = min(arguments.get("concurrent", 3), 10)
    auto_enrich = arguments.get("auto_enrich", True)

    db = SessionLocal()
    try:
        results = await web_scraper_service.scrape_multiple_urls(
            urls=urls, use_ai=True, concurrent=concurrent
        )

        created_properties = []
        errors = []

        for scraped_data in results:
            if not scraped_data.is_valid():
                errors.append(f"{scraped_data.url}: Invalid data")
                continue

            from app.models import Property
            existing = db.query(Property).filter(
                Property.address == scraped_data.address,
                Property.city == scraped_data.city
            ).first()

            if existing:
                errors.append(f"{scraped_data.url}: Already exists (ID {existing.id})")
                continue

            try:
                result = await web_scraper_service.scrape_and_create_property(
                    db=db, url=scraped_data.url or "", agent_id=agent_id,
                    use_ai=False, auto_enrich=False
                )
                if "error" not in result:
                    created_properties.append(result)
                else:
                    errors.append(f"{scraped_data.url}: {result.get('error')}")
            except Exception as e:
                errors.append(f"{scraped_data.url}: {str(e)}")

        enriched_count = 0
        if auto_enrich and created_properties:
            from app.services.zillow_enrichment import zillow_enrichment_service
            for prop_result in created_properties:
                prop_id = prop_result.get("property_id")
                if prop_id:
                    try:
                        await zillow_enrichment_service.enrich_property(db, prop_id, force=True)
                        enriched_count += 1
                    except Exception as e:
                        errors.append(f"Enrichment for {prop_id}: {str(e)}")

        voice_summary = f"Processed {len(urls)} URLs"
        if created_properties:
            voice_summary += f", created {len(created_properties)} properties"
            if enriched_count:
                voice_summary += f", enriched {enriched_count}"
        if errors:
            voice_summary += f", {len(errors)} errors"
        voice_summary += "."

        if errors:
            voice_summary += "\n\nErrors:\n" + "\n".join(f"- {e}" for e in errors[:10])

        return [TextContent(type="text", text=voice_summary)]
    finally:
        db.close()


async def handle_scrape_redfin(arguments: dict) -> list[TextContent]:
    """Scrape a Redfin listing page and create a property."""
    url = arguments.get("url")
    agent_id = arguments.get("agent_id")
    if not url or not agent_id:
        return [TextContent(type="text", text="Please provide url and agent_id.")]

    auto_enrich = arguments.get("auto_enrich", False)
    db = SessionLocal()
    try:
        result = await web_scraper_service.scrape_and_create_property(
            db=db, url=url, agent_id=agent_id, use_ai=True, auto_enrich=auto_enrich
        )

        if "error" in result:
            return [TextContent(type="text", text=f"Failed to create property from Redfin. {result['error']}")]

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

        return [TextContent(type="text", text=voice_summary)]
    finally:
        db.close()


async def handle_scrape_realtor(arguments: dict) -> list[TextContent]:
    """Scrape a Realtor.com listing page and create a property."""
    url = arguments.get("url")
    agent_id = arguments.get("agent_id")
    if not url or not agent_id:
        return [TextContent(type="text", text="Please provide url and agent_id.")]

    auto_enrich = arguments.get("auto_enrich", False)
    db = SessionLocal()
    try:
        result = await web_scraper_service.scrape_and_create_property(
            db=db, url=url, agent_id=agent_id, use_ai=True, auto_enrich=auto_enrich
        )

        if "error" in result:
            return [TextContent(type="text", text=f"Failed to create property from Realtor.com. {result['error']}")]

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

        return [TextContent(type="text", text=voice_summary)]
    finally:
        db.close()


# ============================================================================
# Tool Registrations
# ============================================================================

register_tool(
    Tool(name="scrape_url", description="Scrape a property website URL and extract structured data without creating a property. Use this to preview what data would be extracted from a URL.", inputSchema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to scrape (Zillow, Redfin, Realtor.com, or any property website)"},
            "use_ai": {"type": "boolean", "description": "Use AI to enhance data extraction (default: true)", "default": True}
        },
        "required": ["url"]
    }),
    handle_scrape_url
)

register_tool(
    Tool(name="scrape_and_create", description="Scrape a property URL and automatically create a new property in the database. Validates data and checks for duplicates.", inputSchema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to scrape (Zillow, Redfin, Realtor.com, etc.)"},
            "agent_id": {"type": "integer", "description": "The agent ID to assign the property to"},
            "use_ai": {"type": "boolean", "description": "Use AI to enhance extraction (default: true)", "default": True},
            "auto_enrich": {"type": "boolean", "description": "Auto-enrich with Zillow data after creating (default: false)", "default": False}
        },
        "required": ["url", "agent_id"]
    }),
    handle_scrape_and_create
)

register_tool(
    Tool(name="scrape_zillow_search", description="Scrape a Zillow search results page and extract data for multiple properties (up to 20). Returns scraped data without creating properties.", inputSchema={
        "type": "object",
        "properties": {
            "search_url": {"type": "string", "description": "The Zillow search results URL (contains /homes/)"},
            "max_properties": {"type": "integer", "description": "Maximum number of properties to extract (default: 20, max: 50)", "default": 20}
        },
        "required": ["search_url"]
    }),
    handle_scrape_zillow_search
)

register_tool(
    Tool(name="scrape_and_create_batch", description="Scrape multiple URLs, create properties from all valid results, and optionally auto-enrich with Zillow data. Best for bulk imports.", inputSchema={
        "type": "object",
        "properties": {
            "urls": {"type": "array", "items": {"type": "string"}, "description": "List of URLs to scrape"},
            "agent_id": {"type": "integer", "description": "The agent ID to assign properties to"},
            "concurrent": {"type": "integer", "description": "Number of concurrent requests (default: 3, max: 10)", "default": 3},
            "auto_enrich": {"type": "boolean", "description": "Auto-enrich all created properties with Zillow data (default: true)", "default": True}
        },
        "required": ["urls", "agent_id"]
    }),
    handle_scrape_and_create_batch
)

register_tool(
    Tool(name="scrape_redfin", description="Scrape a Redfin listing page and create a property. Convenience tool for Redfin URLs.", inputSchema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The Redfin listing URL"},
            "agent_id": {"type": "integer", "description": "The agent ID to assign the property to"},
            "auto_enrich": {"type": "boolean", "description": "Auto-enrich with Zillow data after creating (default: false)", "default": False}
        },
        "required": ["url", "agent_id"]
    }),
    handle_scrape_redfin
)

register_tool(
    Tool(name="scrape_realtor", description="Scrape a Realtor.com listing page and create a property. Convenience tool for Realtor.com URLs.", inputSchema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The Realtor.com listing URL"},
            "agent_id": {"type": "integer", "description": "The agent ID to assign the property to"},
            "auto_enrich": {"type": "boolean", "description": "Auto-enrich with Zillow data after creating (default: false)", "default": False}
        },
        "required": ["url", "agent_id"]
    }),
    handle_scrape_realtor
)
