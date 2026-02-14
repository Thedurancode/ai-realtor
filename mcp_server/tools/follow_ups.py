"""Follow-Up Queue MCP tools — AI-prioritized follow-up queue."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


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
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id.")]

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
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id.")]

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
            "Voice: 'I handled property 5', 'Mark follow-up for property 3 as done'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "The property ID to mark as followed up",
                },
                "note": {
                    "type": "string",
                    "description": "Optional note about what was done",
                },
            },
            "required": ["property_id"],
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
            "Voice: 'Snooze property 5 for 3 days', 'Remind me about property 3 in a week'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "The property ID to snooze",
                },
                "hours": {
                    "type": "number",
                    "description": "Snooze duration in hours (default: 72 = 3 days)",
                    "default": 72,
                },
            },
            "required": ["property_id"],
        },
    ),
    handle_snooze_follow_up,
)
