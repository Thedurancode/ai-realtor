"""Activity timeline MCP tools — unified chronological event feed."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get
from ..utils.property_resolver import resolve_property_id


def _format_timestamp(ts_str: str) -> str:
    """Parse ISO timestamp to readable format."""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d %I:%M %p")
    except Exception:
        return ts_str


async def handle_get_activity_timeline(arguments: dict) -> list[TextContent]:
    """Get activity timeline with optional filters."""
    params: dict = {"limit": arguments.get("limit", 50)}
    if arguments.get("property_id"):
        params["property_id"] = arguments["property_id"]
    if arguments.get("event_types"):
        params["event_types"] = ",".join(arguments["event_types"])
    if arguments.get("search"):
        params["search"] = arguments["search"]

    response = api_get("/activity-timeline/", params=params)
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "No activity found.")
    events = data.get("events", [])
    total = data.get("total_events", 0)

    if not events:
        return [TextContent(type="text", text=voice)]

    text = f"{voice}\n\n"
    for ev in events:
        ts = _format_timestamp(ev["timestamp"])
        prop = f" [#{ev['property_id']}]" if ev.get("property_id") else ""
        text += f"{ts}{prop} {ev['title']} — {ev['description']}\n"

    if total > len(events):
        text += f"\n... and {total - len(events)} more events."

    return [TextContent(type="text", text=text.strip())]


async def handle_get_property_timeline(arguments: dict) -> list[TextContent]:
    """Get activity timeline for a specific property."""
    property_id = resolve_property_id(arguments)

    params: dict = {"limit": arguments.get("limit", 50)}
    response = api_get(f"/activity-timeline/property/{property_id}", params=params)
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "No activity found.")
    events = data.get("events", [])

    if not events:
        return [TextContent(type="text", text=f"No activity found for property {property_id}.")]

    text = f"{voice}\n\n"
    for ev in events:
        ts = _format_timestamp(ev["timestamp"])
        text += f"{ts} — {ev['title']}: {ev['description']}\n"

    return [TextContent(type="text", text=text.strip())]


async def handle_get_recent_activity(arguments: dict) -> list[TextContent]:
    """Get recent activity in last N hours."""
    hours = arguments.get("hours", 24)
    params: dict = {"hours": hours}
    if arguments.get("property_id"):
        params["property_id"] = arguments["property_id"]

    response = api_get("/activity-timeline/recent", params=params)
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "No recent activity.")
    events = data.get("events", [])

    if not events:
        scope = f"for property {arguments['property_id']}" if arguments.get("property_id") else ""
        return [TextContent(type="text", text=f"No activity in the last {hours} hours {scope}.".strip())]

    text = f"{voice}\n\n"
    for ev in events[:25]:
        ts = _format_timestamp(ev["timestamp"])
        text += f"{ts} — {ev['title']}\n"

    return [TextContent(type="text", text=text.strip())]


# ── Registration ──

register_tool(
    Tool(
        name="get_activity_timeline",
        description=(
            "Get unified activity timeline — all events from tool calls, notifications, "
            "notes, tasks, contracts, enrichments, and skip traces in chronological order. "
            "Supports filtering by property, event types, and search. "
            "Voice: 'Show me the timeline', 'What's the activity on the Brooklyn property?', "
            "'Show me all contract events', 'Search timeline for Purchase Agreement'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "Filter to specific property (omit for portfolio-wide, optional if address provided)",
                },
                "address": {
                    "type": "string",
                    "description": "Property address to search for (voice-friendly, e.g., '123 Main Street' or 'the Brooklyn property')",
                },
                "event_types": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["conversation", "notification", "note", "task", "contract", "enrichment", "skip_trace"]},
                    "description": "Filter to specific event types",
                },
                "search": {
                    "type": "string",
                    "description": "Text search across event titles and descriptions",
                },
                "limit": {"type": "number", "description": "Max events (default 50)", "default": 50},
            },
        },
    ),
    handle_get_activity_timeline,
)

register_tool(
    Tool(
        name="get_property_timeline",
        description=(
            "Get complete activity timeline for a specific property. "
            "Voice: 'Show me everything on the Brooklyn property', 'Timeline for 123 Main St', "
            "'What happened on the Miami condo?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "number", "description": "The property ID (optional if address provided)"},
                "address": {
                    "type": "string",
                    "description": "Property address to search for (voice-friendly, e.g., '123 Main Street' or 'the Brooklyn property')",
                },
                "limit": {"type": "number", "description": "Max events (default 50)", "default": 50},
            },
        },
    ),
    handle_get_property_timeline,
)

register_tool(
    Tool(
        name="get_recent_activity",
        description=(
            "Get recent activity in last N hours. Quick view of what happened recently. "
            "Voice: 'What happened today?', 'Recent activity', 'What's new?', "
            "'Show me the last 48 hours for the Brooklyn property'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "number", "description": "Filter to specific property (omit for portfolio-wide, optional if address provided)"},
                "address": {
                    "type": "string",
                    "description": "Property address to search for (voice-friendly, e.g., '123 Main Street' or 'the Brooklyn property')",
                },
                "hours": {"type": "number", "description": "Hours to look back (default 24)", "default": 24},
            },
        },
    ),
    handle_get_recent_activity,
)
