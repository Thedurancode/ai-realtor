"""Insights MCP tools — predictive follow-up alerts."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get


async def handle_get_insights(arguments: dict) -> list[TextContent]:
    """Get all actionable alerts across properties."""
    params = {}
    priority = arguments.get("priority")
    if priority:
        params["priority"] = priority

    response = api_get("/insights/", params=params)
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "No insights available.")
    total = data.get("total_alerts", 0)

    if total == 0:
        return [TextContent(type="text", text=voice)]

    text = f"{voice}\n\n"
    for prio in ["urgent", "high", "medium", "low"]:
        items = data.get(prio) or data.get("alerts", [])
        if not items:
            continue
        if prio in data:
            text += f"[{prio.upper()}]\n"
            for a in items:
                text += f"  Property #{a['property_id']} ({a['property_address']}): {a['message']}\n"
                text += f"    → {a['suggested_action']}\n"
            text += "\n"

    return [TextContent(type="text", text=text.strip())]


async def handle_get_property_insights(arguments: dict) -> list[TextContent]:
    """Get alerts for a specific property."""
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id.")]

    response = api_get(f"/insights/property/{property_id}")
    response.raise_for_status()
    data = response.json()

    total = data.get("total_alerts", 0)
    voice = data.get("voice_summary", "No insights.")

    if total == 0:
        return [TextContent(type="text", text=f"Property {property_id} looks good — no issues found.")]

    text = f"{voice}\n\n"
    for prio in ["urgent", "high", "medium", "low"]:
        items = data.get(prio, [])
        for a in items:
            text += f"[{prio.upper()}] {a['message']} → {a['suggested_action']}\n"

    return [TextContent(type="text", text=text.strip())]


# ── Registration ──

register_tool(
    Tool(
        name="get_insights",
        description=(
            "Get actionable alerts across all properties. Surfaces stale properties, "
            "contract deadlines, unsigned contracts, missing enrichments, and high-scoring "
            "properties without action. Voice: 'What needs my attention?', 'Any alerts?', "
            "'What should I follow up on?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "priority": {
                    "type": "string",
                    "enum": ["urgent", "high", "medium", "low"],
                    "description": "Filter by priority level",
                },
            },
        },
    ),
    handle_get_insights,
)

register_tool(
    Tool(
        name="get_property_insights",
        description=(
            "Get alerts for a specific property — overdue contracts, missing data, "
            "stale activity. Voice: 'What's overdue on property 5?', "
            "'Any issues with 123 Main St?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "The property ID to check",
                },
            },
            "required": ["property_id"],
        },
    ),
    handle_get_property_insights,
)
