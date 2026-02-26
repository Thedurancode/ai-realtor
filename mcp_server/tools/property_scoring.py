"""Property scoring MCP tools — multi-dimensional deal quality scoring."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post
from ..utils.property_resolver import resolve_property_id


async def handle_score_property(arguments: dict) -> list[TextContent]:
    """Score a single property."""
    property_id = resolve_property_id(arguments)

    response = api_post(f"/scoring/property/{property_id}")
    response.raise_for_status()
    data = response.json()

    if data.get("error"):
        return [TextContent(type="text", text=data["error"])]

    voice = data.get("voice_summary", "")
    dims = data.get("dimensions", {})

    text = voice
    dim_parts = []
    for dim_name, dim_data in dims.items():
        dim_parts.append(f"{dim_name} {dim_data['score']}/100 ({dim_data['weight']*100:.0f}%)")
    if dim_parts:
        text += f"\n\nBreakdown: {', '.join(dim_parts)}."

    return [TextContent(type="text", text=text.strip())]


async def handle_get_score_breakdown(arguments: dict) -> list[TextContent]:
    """Get stored score breakdown for a property."""
    property_id = resolve_property_id(arguments)

    response = api_get(f"/scoring/property/{property_id}")
    response.raise_for_status()
    data = response.json()

    if data.get("error"):
        return [TextContent(type="text", text=data["error"])]

    addr = data.get('address', f'property #{property_id}')
    text = f"{addr} — {data['score']}/100, Grade {data['grade']}."

    breakdown = data.get("breakdown", {})
    if isinstance(breakdown, dict):
        dims = breakdown.get("dimensions", {})
        if dims:
            dim_parts = [f"{name} {d.get('score', 'N/A')}/100 ({d.get('weight', 0)*100:.0f}%)" for name, d in dims.items()]
            text += f" Breakdown: {', '.join(dim_parts)}."

    return [TextContent(type="text", text=text)]


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
    dist = data.get("grade_distribution", {})
    dist_parts = [f"{grade}: {count}" for grade, count in dist.items() if count > 0]
    text = f"{voice}"
    if dist_parts:
        text += f" Grades: {', '.join(dist_parts)}."

    results = data.get("results", [])
    text += "\n\n"
    for r in results[:10]:
        if "score" in r:
            text += f"#{r['property_id']} {r.get('address', '')} — {r['score']}/100 ({r['grade']})\n"
        elif "error" in r:
            text += f"#{r['property_id']}: error — {r['error']}\n"

    if len(results) > 10:
        text += f"... and {len(results) - 10} more.\n"

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

    text = f"Top {len(data)} properties by score.\n\n"
    for i, prop in enumerate(data, 1):
        price_str = f"${prop['price']:,.0f}" if prop.get("price") else "N/A"
        text += f"{i}. #{prop['property_id']} {prop.get('address', '')} — {prop['score']}/100 Grade {prop['grade']}, {price_str}\n"

    return [TextContent(type="text", text=text.strip())]


# ── Registration ──

register_tool(
    Tool(
        name="score_property",
        description=(
            "Score a property using the 4-dimension scoring engine (Market, Financial, Readiness, Engagement). "
            "Recalculates and saves the score. "
            "Voice: 'Score the Brooklyn property', 'Rate 123 Main St', 'How good is the Miami condo?', 'Grade the Austin house'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "number", "description": "The property ID to score (optional if address provided)"},
                "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street' or 'the Brooklyn property')"},
            },
        },
    ),
    handle_score_property,
)

register_tool(
    Tool(
        name="get_score_breakdown",
        description=(
            "Get the stored score breakdown for a property without recalculating. "
            "Voice: 'Show me the score breakdown for 123 Main St', 'What's the score on the Brooklyn property?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "number", "description": "The property ID (optional if address provided)"},
                "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street' or 'the Brooklyn property')"},
            },
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
                        "status": {"type": "string", "enum": ["new_property", "enriched", "researched", "waiting_for_contracts", "complete"]},
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
