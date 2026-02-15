"""Property scoring MCP tools — multi-dimensional deal quality scoring."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_score_property(arguments: dict) -> list[TextContent]:
    """Score a single property."""
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id.")]

    response = api_post(f"/scoring/property/{property_id}")
    response.raise_for_status()
    data = response.json()

    if data.get("error"):
        return [TextContent(type="text", text=data["error"])]

    voice = data.get("voice_summary", "")
    dims = data.get("dimensions", {})

    text = f"{voice}\n\nSCORE BREAKDOWN — Property #{property_id}\n{'=' * 40}\n"
    text += f"Overall: {data['score']}/100 (Grade {data['grade']})\n\n"

    for dim_name, dim_data in dims.items():
        text += f"  {dim_name.upper()} ({dim_data['weight']*100:.0f}% weight): {dim_data['score']}/100\n"
        for key, val in dim_data.items():
            if key not in ("score", "weight") and isinstance(val, (int, float)):
                text += f"    - {key}: {val}\n"
        text += "\n"

    return [TextContent(type="text", text=text.strip())]


async def handle_get_score_breakdown(arguments: dict) -> list[TextContent]:
    """Get stored score breakdown for a property."""
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id.")]

    response = api_get(f"/scoring/property/{property_id}")
    response.raise_for_status()
    data = response.json()

    if data.get("error"):
        return [TextContent(type="text", text=data["error"])]

    text = f"SCORE — Property #{property_id} ({data.get('address', '')})\n{'=' * 40}\n"
    text += f"Score: {data['score']}/100 | Grade: {data['grade']}\n\n"

    breakdown = data.get("breakdown", {})
    if isinstance(breakdown, dict):
        dims = breakdown.get("dimensions", {})
        if dims:
            for dim_name, dim_data in dims.items():
                text += f"  {dim_name.upper()}: {dim_data.get('score', 'N/A')}/100 (weight {dim_data.get('weight', 0)*100:.0f}%)\n"

    return [TextContent(type="text", text=text.strip())]


async def handle_bulk_score(arguments: dict) -> list[TextContent]:
    """Score multiple properties."""
    body: dict = {}
    if arguments.get("property_ids"):
        body["property_ids"] = arguments["property_ids"]
    if arguments.get("filters"):
        body["filters"] = arguments["filters"]

    response = api_post("/scoring/bulk", json=body)
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "Bulk scoring complete.")
    text = f"{voice}\n\nBULK SCORE RESULTS\n{'=' * 40}\n"
    text += f"Total: {data.get('total', 0)} | Average: {data.get('average_score', 0)}\n\n"

    dist = data.get("grade_distribution", {})
    if dist:
        text += "Grade Distribution:\n"
        for grade, count in dist.items():
            if count > 0:
                text += f"  {grade}: {count}\n"
        text += "\n"

    results = data.get("results", [])
    for r in results[:10]:
        if "score" in r:
            text += f"  #{r['property_id']} {r.get('address', '')}: {r['score']} ({r['grade']})\n"
        elif "error" in r:
            text += f"  #{r['property_id']}: ERROR - {r['error']}\n"

    if len(results) > 10:
        text += f"\n  ... and {len(results) - 10} more\n"

    return [TextContent(type="text", text=text.strip())]


async def handle_get_top_properties(arguments: dict) -> list[TextContent]:
    """Get top-scored properties."""
    params: dict = {"limit": arguments.get("limit", 10)}
    if arguments.get("min_score"):
        params["min_score"] = arguments["min_score"]

    response = api_get("/scoring/top", params=params)
    response.raise_for_status()
    data = response.json()

    if not data:
        return [TextContent(type="text", text="No scored properties found. Score some properties first.")]

    text = f"TOP {len(data)} PROPERTIES BY SCORE\n{'=' * 40}\n\n"
    for i, prop in enumerate(data, 1):
        price_str = f"${prop['price']:,.0f}" if prop.get("price") else "N/A"
        text += (
            f"{i}. #{prop['property_id']} {prop.get('address', '')} ({prop.get('city', '')})\n"
            f"   Score: {prop['score']}/100 | Grade: {prop['grade']} | Price: {price_str}\n\n"
        )

    return [TextContent(type="text", text=text.strip())]


# ── Registration ──

register_tool(
    Tool(
        name="score_property",
        description=(
            "Score a property using the 4-dimension scoring engine (Market, Financial, Readiness, Engagement). "
            "Recalculates and saves the score. "
            "Voice: 'Score property 5', 'Rate this deal', 'How good is property 5?', 'Grade property 3'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "number", "description": "The property ID to score"},
            },
            "required": ["property_id"],
        },
    ),
    handle_score_property,
)

register_tool(
    Tool(
        name="get_score_breakdown",
        description=(
            "Get the stored score breakdown for a property without recalculating. "
            "Voice: 'Show me the score breakdown for property 5', 'What's the score on property 3?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "number", "description": "The property ID"},
            },
            "required": ["property_id"],
        },
    ),
    handle_get_score_breakdown,
)

register_tool(
    Tool(
        name="bulk_score_properties",
        description=(
            "Score multiple properties at once. Optionally filter by property IDs or filters. "
            "Voice: 'Score all my properties', 'Rate everything', 'Bulk score available properties'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_ids": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Specific property IDs to score (omit for all)",
                },
                "filters": {
                    "type": "object",
                    "description": "Optional filters: {status, city}",
                    "properties": {
                        "status": {"type": "string", "enum": ["available", "pending", "sold", "rented", "off_market"]},
                        "city": {"type": "string"},
                    },
                },
            },
        },
    ),
    handle_bulk_score,
)

register_tool(
    Tool(
        name="get_top_properties",
        description=(
            "Get the highest-scored properties in your portfolio. "
            "Voice: 'What are my best deals?', 'Top properties', 'Show me A-grade deals', "
            "'Best investment opportunities'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {"type": "number", "description": "Number of properties to return (default 10)", "default": 10},
                "min_score": {"type": "number", "description": "Minimum score threshold (default 0)", "default": 0},
            },
        },
    ),
    handle_get_top_properties,
)
