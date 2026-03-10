"""Address autocomplete and details — resolve partial addresses to full, validated results."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_post


async def handle_autocomplete_address(arguments: dict) -> list[TextContent]:
    """Autocomplete a partial address string into matching suggestions."""
    query = arguments.get("query", "")
    if not query:
        return [TextContent(type="text", text="Error: 'query' is required (partial address string).")]

    response = api_post("/address/autocomplete", params={"query": query})
    response.raise_for_status()
    data = response.json()

    suggestions = data.get("suggestions", [])
    if not suggestions:
        return [TextContent(type="text", text=f"No address suggestions found for '{query}'.")]

    lines = [f"Found {len(suggestions)} suggestion(s) for '{query}':\n"]
    for i, s in enumerate(suggestions, 1):
        desc = s.get("description", s.get("address", ""))
        place_id = s.get("place_id", "")
        lines.append(f"  {i}. {desc}  (place_id: {place_id})")

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_address_details(arguments: dict) -> list[TextContent]:
    """Get full structured details for a place_id returned by autocomplete."""
    place_id = arguments.get("place_id", "")
    if not place_id:
        return [TextContent(type="text", text="Error: 'place_id' is required. Run autocomplete_address first to obtain one.")]

    response = api_post("/address/details", params={"place_id": place_id})
    response.raise_for_status()
    data = response.json()

    parts = []
    for key in ("street", "city", "state", "zip", "county", "country", "lat", "lng", "formatted_address"):
        val = data.get(key)
        if val is not None:
            parts.append(f"  {key}: {val}")

    if not parts:
        return [TextContent(type="text", text=f"Address details returned empty for place_id '{place_id}'.")]

    return [TextContent(type="text", text=f"Address details:\n" + "\n".join(parts))]


register_tool(
    Tool(
        name="autocomplete_address",
        description="Autocomplete a partial address into a list of suggestions with place_id values. "
                    "Use this when the user types or says a partial address and you need to resolve it. "
                    "Follow up with get_address_details to get the full structured address.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Partial address string to autocomplete (e.g. '123 Main St, New')",
                },
            },
            "required": ["query"],
        },
    ),
    handle_autocomplete_address,
)

register_tool(
    Tool(
        name="get_address_details",
        description="Get full structured address details (street, city, state, zip, county, lat/lng) "
                    "for a place_id obtained from autocomplete_address. Use this to resolve an autocomplete "
                    "suggestion into a complete, validated address before creating a property or mailing.",
        inputSchema={
            "type": "object",
            "properties": {
                "place_id": {
                    "type": "string",
                    "description": "The place_id from an autocomplete_address suggestion",
                },
            },
            "required": ["place_id"],
        },
    ),
    handle_address_details,
)
