"""Property comparison MCP tool — compare 2-5 properties side by side."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get
from ..utils.property_resolver import find_property_by_address


async def handle_compare_properties(arguments: dict) -> list[TextContent]:
    """Compare multiple properties side by side."""
    property_ids = arguments.get("property_ids", [])
    addresses = arguments.get("addresses", [])

    # Resolve addresses to IDs
    for addr in addresses:
        try:
            pid = find_property_by_address(addr)
            if pid not in property_ids:
                property_ids.append(pid)
        except ValueError as e:
            return [TextContent(type="text", text=f"Could not resolve '{addr}': {e}")]

    if len(property_ids) < 2:
        return [TextContent(type="text", text="Please provide at least 2 property IDs or addresses to compare.")]

    ids_str = ",".join(str(pid) for pid in property_ids)
    response = api_get(f"/property-comparison/compare?property_ids={ids_str}")
    response.raise_for_status()
    data = response.json()

    return [TextContent(type="text", text=data.get("voice_summary", "Comparison complete."))]


# ── Registration ──

register_tool(
    Tool(
        name="compare_properties",
        description=(
            "Compare 2-5 properties side by side. Shows price, size, deal grades, "
            "ROI, cash flow, and picks a winner. "
            "Voice: 'Compare properties 1, 3, and 7' or "
            "'Compare the Brooklyn property with the Queens one'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_ids": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of property IDs to compare (2-5)",
                },
                "addresses": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of property addresses to compare (resolved to IDs)",
                },
            },
        },
    ),
    handle_compare_properties,
)
