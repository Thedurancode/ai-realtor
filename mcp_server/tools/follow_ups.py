"""Follow-Up Queue MCP tools — AI-prioritized follow-up queue."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post
from ..utils.property_resolver import resolve_property_id


async def handle_get_follow_up_queue(arguments: dict) -> list[TextContent]:
    """Get ranked follow-up queue."""
    params = {}
    limit = arguments.get("limit", 10)
    if limit:
        params["limit"] = limit
    priority = arguments.get("priority")
    if priority:
        params["priority"] = priority

    response = api_get("/follow-ups/queue", params=params)
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "No follow-ups.")
    items = data.get("items", [])
    total = data.get("total", 0)

    if total == 0:
        return [TextContent(type="text", text=voice)]

    text = f"{voice}\n\n"
    for item in items:
        rank = item.get("rank", "")
        addr = item["address"]
        prio = item["priority"].upper()
        score = item["score"]
        text += f"#{rank} [{prio}] Property #{item['property_id']} — {addr} (score: {score})\n"
        for reason in item.get("reasons", []):
            text += f"   • {reason}\n"
        action = item.get("suggested_action")
        if action:
            text += f"   → {action}\n"
        contact = item.get("contact")
        if contact and contact.get("phone"):
            text += f"   📞 {contact['name']} ({contact['role']}): {contact['phone']}\n"
        text += "\n"

    return [TextContent(type="text", text=text.strip())]


async def handle_complete_follow_up(arguments: dict) -> list[TextContent]:
    """Mark a follow-up as completed."""
    property_id = resolve_property_id(arguments)

    note = arguments.get("note")
    body = {}
    if note:
        body["note"] = note

    response = api_post(f"/follow-ups/{property_id}/complete", json=body)
    response.raise_for_status()
    data = response.json()

    if data.get("error"):
        return [TextContent(type="text", text=f"Error: {data['error']}")]

    addr = data.get("address", f"property #{property_id}")
    msg = f"Follow-up for {addr} marked as done."
    if note:
        msg += f" Note saved: {note}"
    return [TextContent(type="text", text=msg)]


async def handle_snooze_follow_up(arguments: dict) -> list[TextContent]:
    """Snooze a follow-up for a specified duration."""
    property_id = resolve_property_id(arguments)

    hours = arguments.get("hours", 72)
    response = api_post(f"/follow-ups/{property_id}/snooze", json={"hours": hours})
    response.raise_for_status()
    data = response.json()

    if data.get("error"):
        return [TextContent(type="text", text=f"Error: {data['error']}")]

    addr = data.get("address", f"property #{property_id}")
    label = data.get("label", f"{hours}h")
    return [TextContent(type="text", text=f"Follow-up for {addr} snoozed for {label}. I'll remind you then.")]


# ── Registration ──

register_tool(
    Tool(
        name="get_follow_up_queue",
        description=(
            "Get your AI-prioritized follow-up queue — ranked list of properties and contacts "
            "needing attention. Scored by activity staleness, deal grade, unsigned contracts, "
            "missed outreach, and overdue tasks. "
            "Voice: 'What should I work on next?', 'Who do I need to call?', "
            "'What's my top priority?', 'Show me my follow-up queue'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "number",
                    "description": "Max items to return (default: 10, max: 25)",
                    "default": 10,
                },
                "priority": {
                    "type": "string",
                    "enum": ["urgent", "high", "medium", "low"],
                    "description": "Filter by priority level",
                },
            },
        },
    ),
    handle_get_follow_up_queue,
)

register_tool(
    Tool(
        name="complete_follow_up",
        description=(
            "Mark a follow-up as completed. Logs the action and optionally saves a note. "
            "Voice: 'I handled the Brooklyn property', 'Mark follow-up for 123 Main St as done'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "The property ID to mark as followed up (optional if address provided)",
                },
                "address": {
                    "type": "string",
                    "description": "Property address to search for (voice-friendly, e.g., '123 Main Street' or 'the Brooklyn property')",
                },
                "note": {
                    "type": "string",
                    "description": "Optional note about what was done",
                },
            },
        },
    ),
    handle_complete_follow_up,
)

register_tool(
    Tool(
        name="snooze_follow_up",
        description=(
            "Snooze a property's follow-up for a specified duration. The property will "
            "reappear in the queue after the snooze period. "
            "Voice: 'Snooze the Brooklyn property for 3 days', 'Remind me about 123 Main St in a week'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "The property ID to snooze (optional if address provided)",
                },
                "address": {
                    "type": "string",
                    "description": "Property address to search for (voice-friendly, e.g., '123 Main Street' or 'the Brooklyn property')",
                },
                "hours": {
                    "type": "number",
                    "description": "Snooze duration in hours (default: 72 = 3 days)",
                    "default": 72,
                },
            },
        },
    ),
    handle_snooze_follow_up,
)
