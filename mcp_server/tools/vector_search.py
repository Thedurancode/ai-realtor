"""Vector search MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post
from ..utils.property_resolver import find_property_by_address


# ── Handlers ──

async def handle_semantic_search(arguments: dict) -> list[TextContent]:
    query = arguments.get("query")
    if not query:
        return [TextContent(type="text", text="Please provide a search query.")]

    payload = {"query": query, "limit": arguments.get("limit", 10)}
    if arguments.get("status"):
        payload["status"] = arguments["status"]
    if arguments.get("property_type"):
        payload["property_type"] = arguments["property_type"]
    if arguments.get("min_price"):
        payload["min_price"] = arguments["min_price"]
    if arguments.get("max_price"):
        payload["max_price"] = arguments["max_price"]

    response = api_post("/search/properties", json=payload)
    response.raise_for_status()
    data = response.json()

    text = data.get("voice_summary", f"Found {data.get('count', 0)} results.")
    text += "\n\n"
    for i, r in enumerate(data.get("results", []), 1):
        text += f"{i}. {r['address']}"
        if r.get("price"):
            text += f" — ${r['price']:,.0f}"
        if r.get("bedrooms"):
            text += f" | {r['bedrooms']}bd"
        if r.get("bathrooms"):
            text += f"/{r['bathrooms']}ba"
        if r.get("square_feet"):
            text += f" | {r['square_feet']} sqft"
        text += f" | {r.get('similarity', 0):.0%} match"
        text += "\n"
    return [TextContent(type="text", text=text)]


async def handle_find_similar_properties(arguments: dict) -> list[TextContent]:
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    if not property_id and address:
        property_id = find_property_by_address(address)
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id or address.")]

    limit = arguments.get("limit", 5)
    response = api_get(f"/search/similar/{property_id}", params={"limit": limit})
    response.raise_for_status()
    data = response.json()

    text = data.get("voice_summary", f"Found {data.get('count', 0)} similar properties.")
    text += "\n\n"
    for i, r in enumerate(data.get("similar", []), 1):
        text += f"{i}. {r['address']}"
        if r.get("price"):
            text += f" — ${r['price']:,.0f}"
        if r.get("bedrooms"):
            text += f" | {r['bedrooms']}bd"
        if r.get("bathrooms"):
            text += f"/{r['bathrooms']}ba"
        text += f" | {r.get('similarity', 0):.0%} match"
        text += "\n"
    return [TextContent(type="text", text=text)]


async def handle_search_research(arguments: dict) -> list[TextContent]:
    query = arguments.get("query")
    if not query:
        return [TextContent(type="text", text="Please provide a search query.")]

    payload = {
        "query": query,
        "dossier_limit": arguments.get("dossier_limit", 5),
        "evidence_limit": arguments.get("evidence_limit", 10),
    }
    response = api_post("/search/research", json=payload)
    response.raise_for_status()
    data = response.json()

    text = data.get("voice_summary", "No results found.")
    text += "\n\n"
    dossiers = data.get("dossiers", [])
    if dossiers:
        text += "Dossiers:\n"
        for i, d in enumerate(dossiers, 1):
            text += f"  {i}. Research #{d['research_property_id']} ({d.get('similarity', 0):.0%} match) — {d.get('snippet', '')}\n"
        text += "\n"
    evidence = data.get("evidence", [])
    if evidence:
        text += "Evidence:\n"
        for i, e in enumerate(evidence, 1):
            text += f"  {i}. [{e.get('category', '')}] {e['claim']} ({e.get('similarity', 0):.0%} match)\n"
    return [TextContent(type="text", text=text.strip())]


# ── Tool Registration ──

register_tool(Tool(name="semantic_search", description="Search properties using natural language semantic search powered by AI embeddings. Voice: 'Find modern condos in Brooklyn with parking' or 'Search for houses under 500K near good schools'.", inputSchema={"type": "object", "properties": {"query": {"type": "string", "description": "Natural language search query"}, "limit": {"type": "number", "description": "Max results (default 10)", "default": 10}, "status": {"type": "string", "description": "Filter by status: available, pending, sold"}, "property_type": {"type": "string", "description": "Filter by type: house, condo, apartment, townhouse, land, commercial"}, "min_price": {"type": "number", "description": "Minimum price filter"}, "max_price": {"type": "number", "description": "Maximum price filter"}}, "required": ["query"]}), handle_semantic_search)

register_tool(Tool(name="find_similar_properties", description="Find properties similar to a given property using AI vector similarity. Voice: 'Find properties similar to property 5' or 'Show me listings like the one on Main Street'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID to find similar properties for"}, "address": {"type": "string", "description": "Property address to find similar properties for"}, "limit": {"type": "number", "description": "Max results (default 5)", "default": 5}}}), handle_find_similar_properties)

register_tool(Tool(name="search_research", description="Search across all research dossiers and evidence items using semantic search. Voice: 'Find research about flood zones in Miami' or 'What do we know about school ratings near Brooklyn?'.", inputSchema={"type": "object", "properties": {"query": {"type": "string", "description": "Natural language search query"}, "dossier_limit": {"type": "number", "description": "Max dossiers to return (default 5)", "default": 5}, "evidence_limit": {"type": "number", "description": "Max evidence items to return (default 10)", "default": 10}}, "required": ["query"]}), handle_search_research)
