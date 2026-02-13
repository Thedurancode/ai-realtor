"""Property management MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post, api_patch
from ..utils.property_resolver import resolve_property_id, find_property_by_address


# ── Helpers ──

async def list_properties(limit: int = 10, status=None, property_type=None, city=None, min_price=None, max_price=None, bedrooms=None) -> dict:
    params = {"limit": limit}
    if status:
        params["status"] = status
    if property_type:
        params["property_type"] = property_type
    if city:
        params["city"] = city
    if min_price is not None:
        params["min_price"] = min_price
    if max_price is not None:
        params["max_price"] = max_price
    if bedrooms is not None:
        params["bedrooms"] = bedrooms
    response = api_get("/properties/", params=params)
    response.raise_for_status()
    return response.json()


async def get_property(property_id: int) -> dict:
    response = api_get(f"/properties/{property_id}")
    response.raise_for_status()
    return response.json()


async def create_property_with_address(address, price, bedrooms=None, bathrooms=None, agent_id=1) -> dict:
    autocomplete_resp = api_post("/address/autocomplete", json={"input": address, "country": "us"})
    autocomplete_resp.raise_for_status()
    suggestions = autocomplete_resp.json()['suggestions']
    if not suggestions:
        raise ValueError(f"No address found for: {address}")
    place_id = suggestions[0]['place_id']
    create_resp = api_post("/context/property/create", json={
        "place_id": place_id, "price": price, "bedrooms": bedrooms,
        "bathrooms": bathrooms, "agent_id": agent_id, "session_id": "mcp_session"
    })
    create_resp.raise_for_status()
    return create_resp.json()


async def update_property(property_id=None, address_query=None, **fields) -> dict:
    if address_query and not property_id:
        property_id = find_property_by_address(address_query)
    if not property_id:
        raise ValueError("Provide either a property_id or address to update")
    update_data = {k: v for k, v in fields.items() if v is not None}
    if not update_data:
        raise ValueError("No fields to update")
    response = api_patch(f"/properties/{property_id}", json=update_data)
    response.raise_for_status()
    return response.json()


async def delete_property(property_id: int) -> dict:
    from app.database import SessionLocal
    from app.models.property import Property
    from app.models.zillow_enrichment import ZillowEnrichment
    from app.models.skip_trace import SkipTrace
    from app.models.contact import Contact
    from app.models.contract import Contract

    db = SessionLocal()
    try:
        property = db.query(Property).filter(Property.id == property_id).first()
        if not property:
            raise ValueError(f"Property {property_id} not found")
        address = property.address
        db.query(Contract).filter(Contract.property_id == property_id).delete()
        db.query(Contact).filter(Contact.property_id == property_id).delete()
        db.query(ZillowEnrichment).filter(ZillowEnrichment.property_id == property_id).delete()
        db.query(SkipTrace).filter(SkipTrace.property_id == property_id).delete()
        db.delete(property)
        db.commit()
        return {"success": True, "message": f"Deleted property {property_id} ({address})", "property_id": property_id, "address": address}
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


async def enrich_property(property_id: int) -> dict:
    response = api_post("/context/enrich", json={"property_ref": str(property_id), "session_id": "mcp_session"})
    response.raise_for_status()
    return response.json()


# ── Handlers ──

async def handle_list_properties(arguments: dict) -> list[TextContent]:
    limit = arguments.get("limit", 10)
    status = arguments.get("status")
    property_type = arguments.get("property_type")
    city = arguments.get("city")
    min_price = arguments.get("min_price")
    max_price = arguments.get("max_price")
    bedrooms = arguments.get("bedrooms")
    result = await list_properties(
        limit=limit, status=status, property_type=property_type,
        city=city, min_price=min_price, max_price=max_price, bedrooms=bedrooms,
    )

    if not result:
        text = f"No {status} properties found." if status else "No properties found."
    else:
        text = f"Found {len(result)} property(ies):\n\n"
        for p in result:
            price_str = f"${p['price']:,.0f}" if p.get('price') else "price not set"
            text += f"Property {p['id']}: {p.get('address', 'N/A')}, {p.get('city', '')}, {p.get('state', '')}\n"
            text += f"  Price: {price_str}"
            if p.get('bedrooms') or p.get('bathrooms'):
                text += f" | {p.get('bedrooms', '?')} bed / {p.get('bathrooms', '?')} bath"
            if p.get('square_footage'):
                text += f" | {p['square_footage']:,.0f} sqft"
            text += f"\n  Status: {p.get('status', 'available')}"
            if p.get('deal_score') is not None:
                text += f" | Deal Score: {p['deal_score']:.0f}/100 (Grade {p.get('score_grade', '?')})"
            if p.get('pipeline_status'):
                text += f" | Pipeline: {p['pipeline_status']}"
            text += "\n\n"

    return [TextContent(type="text", text=text)]


async def handle_get_property(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    result = await get_property(property_id)

    price_str = f"${result['price']:,.0f}" if result.get('price') else "price not set"
    text = f"Property {result['id']}: {result.get('address', 'N/A')}, {result.get('city', '')}, {result.get('state', '')} {result.get('zip_code', '')}\n\n"
    text += f"Price: {price_str}\n"
    if result.get('bedrooms'):
        text += f"Bedrooms: {result['bedrooms']}\n"
    if result.get('bathrooms'):
        text += f"Bathrooms: {result['bathrooms']}\n"
    if result.get('square_footage'):
        text += f"Square footage: {result['square_footage']:,.0f}\n"
    text += f"Status: {result.get('status', 'available')}\n"
    if result.get('property_type'):
        text += f"Type: {result['property_type']}\n"

    if result.get('deal_score') is not None:
        text += f"\nDEAL SCORE: {result['deal_score']:.0f}/100 (Grade {result.get('score_grade', '?')})\n"
        breakdown = result.get('score_breakdown', {})
        if breakdown:
            for component, score in breakdown.items():
                label = component.replace('_', ' ').title()
                text += f"  {label}: {score:.0f}/100\n"
    if result.get('pipeline_status'):
        text += f"Pipeline: {result['pipeline_status']}\n"

    enrichment = result.get('zillow_enrichment')
    if enrichment:
        text += "\nZILLOW DATA:\n"
        if enrichment.get('zestimate'):
            text += f"Zestimate: ${enrichment['zestimate']:,.0f}\n"
        if enrichment.get('rent_zestimate'):
            text += f"Rent estimate: ${enrichment['rent_zestimate']:,.0f}/month\n"
        if enrichment.get('year_built'):
            text += f"Year built: {enrichment['year_built']}\n"
        if enrichment.get('home_type'):
            text += f"Home type: {enrichment['home_type']}\n"
        if enrichment.get('living_area'):
            text += f"Living area: {enrichment['living_area']:,.0f} sqft\n"
        if enrichment.get('lot_size'):
            units = enrichment.get('lot_area_units', 'sqft')
            text += f"Lot size: {enrichment['lot_size']:,.1f} {units}\n"
        if enrichment.get('property_tax_rate'):
            text += f"Property tax rate: {enrichment['property_tax_rate']}%\n"
        if enrichment.get('annual_tax_amount'):
            text += f"Annual taxes: ${enrichment['annual_tax_amount']:,.0f}\n"
        if enrichment.get('description'):
            text += f"Description: {enrichment['description']}\n"
        photos = enrichment.get('photos', [])
        if photos:
            text += f"Photos: {len(photos)} available\n"
        schools = enrichment.get('schools', [])
        if schools:
            text += f"\nNearby schools:\n"
            for s in schools[:3]:
                rating = f" (rating: {s['rating']}/10)" if s.get('rating') else ""
                text += f"  - {s.get('name', 'Unknown')}{rating}\n"
        tax_history = enrichment.get('tax_history', [])
        if tax_history:
            text += f"\nTax history ({len(tax_history)} years):\n"
            for t in tax_history[:3]:
                text += f"  - {t.get('year', '?')}: ${t.get('value', 0):,.0f} (tax: ${t.get('tax', 0):,.0f})\n"

    skip_traces = result.get('skip_traces', [])
    if skip_traces:
        trace = skip_traces[0]
        text += "\nOWNER INFO (Skip Trace):\n"
        if trace.get('owner_name'):
            text += f"Owner: {trace['owner_name']}\n"
        phones = trace.get('phone_numbers', [])
        if phones:
            text += f"Phone numbers: {', '.join(phones)}\n"
        emails = trace.get('emails', [])
        if emails:
            text += f"Emails: {', '.join(emails)}\n"
        if trace.get('mailing_address'):
            mailing = trace['mailing_address']
            if trace.get('mailing_city'):
                mailing += f", {trace['mailing_city']}"
            if trace.get('mailing_state'):
                mailing += f", {trace['mailing_state']}"
            text += f"Mailing address: {mailing}\n"

    return [TextContent(type="text", text=text)]


async def handle_create_property(arguments: dict) -> list[TextContent]:
    result = await create_property_with_address(
        address=arguments["address"], price=arguments["price"],
        bedrooms=arguments.get("bedrooms"), bathrooms=arguments.get("bathrooms"),
        agent_id=arguments.get("agent_id", 1)
    )
    data = result.get("data", result)
    prop_id = data.get("property_id", data.get("id", "?"))
    address = data.get("address", arguments.get("address", "N/A"))
    city = data.get("city", "")
    state = data.get("state", "")
    price = data.get("price", arguments.get("price"))
    price_str = f"${price:,.0f}" if price else ""

    text = f"Property created successfully.\n\n"
    text += f"Property {prop_id}: {address}, {city}, {state}\n"
    text += f"Price: {price_str}\n"
    if arguments.get('bedrooms'):
        text += f"Bedrooms: {arguments['bedrooms']}\n"
    if arguments.get('bathrooms'):
        text += f"Bathrooms: {arguments['bathrooms']}\n"
    text += f"Status: available\n"
    return [TextContent(type="text", text=text)]


async def handle_delete_property(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    result = await delete_property(property_id)
    text = f"Property {property_id} deleted successfully."
    if result.get('address'):
        text = f"Property {property_id} at {result['address']} has been deleted."
    return [TextContent(type="text", text=text)]


async def handle_update_property(arguments: dict) -> list[TextContent]:
    property_id = arguments.pop("property_id", None)
    address_query = arguments.pop("address", None)
    result = await update_property(property_id=property_id, address_query=address_query, **arguments)

    prop_id = result.get('id', property_id or '?')
    address = result.get('address', 'N/A')
    city = result.get('city', '')
    state = result.get('state', '')
    text = f"Property {prop_id} updated successfully.\n\n"
    text += f"Property {prop_id}: {address}, {city}, {state}\n"
    if result.get('price'):
        text += f"Price: ${result['price']:,.0f}\n"
    if result.get('status'):
        text += f"Status: {result['status']}\n"
    if result.get('bedrooms'):
        text += f"Bedrooms: {result['bedrooms']}\n"
    if result.get('bathrooms'):
        text += f"Bathrooms: {result['bathrooms']}\n"
    if result.get('square_footage'):
        text += f"Square footage: {result['square_footage']:,.0f}\n"
    if result.get('property_type'):
        text += f"Type: {result['property_type']}\n"
    if result.get('deal_type'):
        text += f"Deal type: {result['deal_type']}\n"
    return [TextContent(type="text", text=text)]


async def handle_enrich_property(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    result = await enrich_property(property_id)

    enrichment = result.get("data", result.get("enrichment", result))
    address = enrichment.get("property_address", f"property {property_id}")
    text = f"Property {address} enriched with Zillow data.\n\n"

    if enrichment.get('zestimate'):
        text += f"Zestimate: ${enrichment['zestimate']:,.0f}\n"
    if enrichment.get('rent_zestimate'):
        text += f"Rent estimate: ${enrichment['rent_zestimate']:,.0f}/month\n"
    if enrichment.get('year_built'):
        text += f"Year built: {enrichment['year_built']}\n"
    if enrichment.get('home_type'):
        text += f"Home type: {enrichment['home_type']}\n"
    if enrichment.get('living_area'):
        text += f"Living area: {enrichment['living_area']:,.0f} sqft\n"
    if enrichment.get('lot_size'):
        text += f"Lot size: {enrichment['lot_size']:,.1f}\n"
    if enrichment.get('photo_count'):
        text += f"Photos: {enrichment['photo_count']} available\n"
    if enrichment.get('zillow_url'):
        text += f"Zillow: {enrichment['zillow_url']}\n"

    try:
        full = await get_property(property_id)
        full_enrich = full.get('zillow_enrichment', {})
        if full_enrich:
            if full_enrich.get('description'):
                text += f"\nDescription: {full_enrich['description']}\n"
            if full_enrich.get('property_tax_rate'):
                text += f"Property tax rate: {full_enrich['property_tax_rate']}%\n"
            if full_enrich.get('annual_tax_amount'):
                text += f"Annual taxes: ${full_enrich['annual_tax_amount']:,.0f}\n"
            schools = full_enrich.get('schools', [])
            if schools:
                text += f"\nNearby schools:\n"
                for s in schools[:3]:
                    rating = f" (rating: {s['rating']}/10)" if s.get('rating') else ""
                    text += f"  - {s.get('name', 'Unknown')}{rating}\n"
            tax_history = full_enrich.get('tax_history', [])
            if tax_history:
                text += f"\nTax history:\n"
                for t in tax_history[:3]:
                    text += f"  - {t.get('year', '?')}: ${t.get('value', 0):,.0f} (tax: ${t.get('tax', 0):,.0f})\n"
    except Exception:
        pass

    return [TextContent(type="text", text=text)]


# ── Tool Registration ──

register_tool(
    Tool(name="list_properties", description="List all properties in the database. Filter by status, property type, city, price range, or bedrooms. Voice examples: 'show me all condos', 'list houses under 500k in Miami', 'show available land'.", inputSchema={"type": "object", "properties": {"limit": {"type": "number", "description": "Maximum number of properties to return (default: 10)", "default": 10}, "status": {"type": "string", "description": "Filter by property status", "enum": ["available", "pending", "sold", "rented", "off_market"]}, "property_type": {"type": "string", "description": "Filter by property type", "enum": ["house", "condo", "townhouse", "apartment", "land", "commercial", "multi_family"]}, "city": {"type": "string", "description": "Filter by city name (partial match)"}, "min_price": {"type": "number", "description": "Minimum price filter"}, "max_price": {"type": "number", "description": "Maximum price filter"}, "bedrooms": {"type": "number", "description": "Minimum number of bedrooms"}}}),
    handle_list_properties
)

register_tool(
    Tool(name="get_property", description="Get detailed information for a specific property by ID or address. Returns complete property data including Zillow enrichment, skip trace data, photos, schools, tax history, and owner information. Voice-friendly: say the address instead of the ID.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "The ID of the property to retrieve (optional if address provided)"}, "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street' or 'the Hillsborough property')"}}}),
    handle_get_property
)

register_tool(
    Tool(name="create_property", description="Create a new property in the database. Automatically looks up full address details using Google Places API. The property will appear on the TV display.", inputSchema={"type": "object", "properties": {"address": {"type": "string", "description": "Property address (will be autocompleted, e.g., '123 Main St, New York, NY')"}, "price": {"type": "number", "description": "Property price in dollars"}, "bedrooms": {"type": "number", "description": "Number of bedrooms"}, "bathrooms": {"type": "number", "description": "Number of bathrooms"}, "agent_id": {"type": "number", "description": "Agent ID (default: 1)", "default": 1}}, "required": ["address", "price"]}),
    handle_create_property
)

register_tool(
    Tool(name="delete_property", description="Delete a property and all its related data (enrichments, skip traces, contacts, contracts) from the database. This action cannot be undone. Voice-friendly: say the address instead of the ID.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "The ID of the property to delete (optional if address provided)"}, "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street' or 'the Brooklyn property')"}}}),
    handle_delete_property
)

register_tool(
    Tool(name="update_property", description="Update a property's details such as price, status, bedrooms, bathrooms, square footage, property type, or deal type. Can use address or property ID. Example: 'Update the price on 123 Main Street to $900,000' or 'Change the Avondale property status to sold'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "The ID of the property to update (optional if address is provided)"}, "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street' or 'the Avondale property')"}, "price": {"type": "number", "description": "New price in dollars"}, "status": {"type": "string", "description": "New status", "enum": ["available", "pending", "sold", "rented", "off_market"]}, "bedrooms": {"type": "number", "description": "Number of bedrooms"}, "bathrooms": {"type": "number", "description": "Number of bathrooms"}, "square_feet": {"type": "number", "description": "Square footage"}, "property_type": {"type": "string", "description": "Property type", "enum": ["house", "condo", "townhouse", "apartment", "land", "commercial", "multi_family"]}, "deal_type": {"type": "string", "description": "Deal type", "enum": ["traditional", "wholesale", "creative_finance", "subject_to", "novation", "lease_option"]}}}),
    handle_update_property
)

register_tool(
    Tool(name="enrich_property", description="Enrich a property with comprehensive Zillow data including photos, Zestimate, rent estimate, tax history, price history, schools with ratings, property details, and market statistics. Voice-friendly: say the address instead of the ID.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "The ID of the property to enrich (optional if address provided)"}, "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street' or 'the Hillsborough property')"}}}),
    handle_enrich_property
)
