"""Notification MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


# ── Helpers ──

async def send_notification(title, message, notification_type="general", priority="medium", icon="\U0001f514", property_id=None, auto_dismiss_seconds=10) -> dict:
    response = api_post("/notifications/", json={
        "type": notification_type, "priority": priority, "title": title,
        "message": message, "icon": icon, "property_id": property_id,
        "auto_dismiss_seconds": auto_dismiss_seconds
    })
    response.raise_for_status()
    return response.json()


async def list_notifications(limit=10, unread_only=False) -> dict:
    params = {"limit": limit}
    if unread_only:
        params["unread_only"] = "true"
    response = api_get("/notifications/", params=params)
    response.raise_for_status()
    return response.json()


# ── Handlers ──

async def handle_send_notification(arguments: dict) -> list[TextContent]:
    await send_notification(
        title=arguments["title"], message=arguments["message"],
        notification_type=arguments.get("notification_type", "general"),
        priority=arguments.get("priority", "medium"),
        icon=arguments.get("icon", "\U0001f514"),
        property_id=arguments.get("property_id"),
        auto_dismiss_seconds=arguments.get("auto_dismiss_seconds", 10)
    )
    return [TextContent(type="text", text=f"Notification sent to TV display. Title: {arguments['title']}, Message: {arguments['message']}")]


async def handle_list_notifications(arguments: dict) -> list[TextContent]:
    limit = arguments.get("limit", 10)
    unread_only = arguments.get("unread_only", False)
    result = await list_notifications(limit=limit, unread_only=unread_only)

    default_icon = "\U0001f514"  # 🔔 bell emoji
    if isinstance(result, list) and len(result) > 0:
        summary = f"You have {len(result)} notification(s).\n\n"
        for notif in result:
            summary += f"#{notif.get('id', '')} {notif['title']}: {notif['message']} [{notif['priority']}] ({notif['created_at']})\n"
        return [TextContent(type="text", text=summary.strip())]
    else:
        return [TextContent(type="text", text="No notifications found.")]


# ── Tool Registration ──

register_tool(
    Tool(name="send_notification", description="Send a custom notification to the TV display. Use this to alert about important events, milestones, or custom messages. The notification will appear as an animated toast on the TV display.", inputSchema={"type": "object", "properties": {"title": {"type": "string", "description": "Notification title (concise, under 50 chars)"}, "message": {"type": "string", "description": "Notification message"}, "notification_type": {"type": "string", "description": "Type of notification", "enum": ["general", "contract_signed", "new_lead", "property_price_change", "property_status_change", "appointment_reminder", "skip_trace_complete", "enrichment_complete", "follow_up_due", "contract_deadline", "scheduled_task", "pipeline_auto_advance", "daily_digest", "follow_up_queue"], "default": "general"}, "priority": {"type": "string", "description": "Priority level (affects color)", "enum": ["low", "medium", "high", "urgent"], "default": "medium"}, "icon": {"type": "string", "description": "Emoji icon to display (e.g., \U0001f389, \u26a0\ufe0f, \U0001f4dd)", "default": "\U0001f514"}, "property_id": {"type": "number", "description": "Optional property ID to associate"}, "auto_dismiss_seconds": {"type": "number", "description": "Auto-dismiss after X seconds (5-30, default: 10)", "default": 10}}, "required": ["title", "message"]}),
    handle_send_notification
)

register_tool(
    Tool(name="list_notifications", description="List recent notifications from the system. Shows notification history including contracts signed, new leads, price changes, etc.", inputSchema={"type": "object", "properties": {"limit": {"type": "number", "description": "Number of notifications to return (default: 10)", "default": 10}, "unread_only": {"type": "boolean", "description": "Only show unread notifications", "default": False}}}),
    handle_list_notifications
)


# ── Phase 3: Proactive notification tools ──

def _human_time_ago(timestamp_str: str) -> str:
    """Convert ISO timestamp to human-readable 'X ago' format."""
    from datetime import datetime, timezone

    try:
        ts = timestamp_str.replace("Z", "+00:00")
        if "+" not in ts and "-" not in ts[10:]:
            ts += "+00:00"
        timestamp = datetime.fromisoformat(ts)
        now = datetime.now(timezone.utc)
        diff = now - timestamp

        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"{minutes}m ago"
        return "just now"
    except Exception:
        return "recently"


async def handle_get_notification_summary(arguments: dict) -> list[TextContent]:
    """Voice-friendly digest of recent activity."""
    hours = arguments.get("hours", 24)
    result = await list_notifications(limit=50, unread_only=False)

    if not isinstance(result, list) or not result:
        return [TextContent(type="text", text=f"No activity in the last {hours} hours.")]

    # Group by type
    from collections import Counter
    type_counts = Counter()
    urgent_items = []
    for n in result:
        ntype = n.get("type", "general")
        type_counts[ntype] += 1
        if n.get("priority") == "urgent":
            urgent_items.append(n)

    type_labels = {
        "contract_signed": "contracts signed",
        "new_lead": "new leads",
        "property_price_change": "price changes",
        "property_status_change": "status changes",
        "skip_trace_complete": "skip traces completed",
        "enrichment_complete": "enrichments completed",
        "appointment_reminder": "appointment reminders",
        "general": "general notifications",
    }

    # Build conversational summary
    parts = [f"{count} {type_labels.get(ntype, ntype.replace('_', ' '))}" for ntype, count in type_counts.most_common()]
    text = f"Activity summary: {len(result)} events — {', '.join(parts)}."

    if urgent_items:
        text += f" URGENT: {urgent_items[0]['title']}: {urgent_items[0]['message']}."

    recent_parts = [f"{n['title']} ({_human_time_ago(n.get('created_at', ''))})" for n in result[:3]]
    text += f" Most recent: {'; '.join(recent_parts)}."

    return [TextContent(type="text", text=text)]


async def handle_acknowledge_notification(arguments: dict) -> list[TextContent]:
    """Mark notification as read or dismissed."""
    notification_id = arguments["notification_id"]
    action = arguments.get("action", "read")

    response = api_post(f"/notifications/{notification_id}/{action}")
    response.raise_for_status()
    return [TextContent(type="text", text=f"Notification #{notification_id} marked as {action}.")]


async def handle_poll_for_updates(arguments: dict) -> list[TextContent]:
    """Check for new unread notifications — enables proactive assistant behavior."""
    result = await list_notifications(limit=5, unread_only=True)

    if not isinstance(result, list) or not result:
        return [TextContent(type="text", text="No new updates.")]

    count = len(result)
    urgent = [n for n in result if n.get("priority") == "urgent"]

    text = f"You have {count} new update{'s' if count != 1 else ''}. "

    if urgent:
        text += f"URGENT: {urgent[0]['title']}. "
    else:
        text += f"Most recent: {result[0]['title']}. "

    text += "Would you like to hear them all?"
    return [TextContent(type="text", text=text)]


register_tool(
    Tool(
        name="get_notification_summary",
        description="Get a voice-friendly summary of recent activity and notifications. "
                    "Groups events by type (contracts signed, new leads, etc.) and highlights urgent items. "
                    "Voice: 'What happened today?' or 'Give me a summary'",
        inputSchema={
            "type": "object",
            "properties": {
                "hours": {"type": "integer", "default": 24, "description": "Look back this many hours"},
            },
        },
    ),
    handle_get_notification_summary,
)

register_tool(
    Tool(
        name="acknowledge_notification",
        description="Mark a notification as read or dismissed. "
                    "Voice: 'Got it, dismiss notification 5'",
        inputSchema={
            "type": "object",
            "properties": {
                "notification_id": {"type": "integer", "description": "Notification ID to acknowledge"},
                "action": {"type": "string", "enum": ["read", "dismiss"], "default": "read", "description": "Mark as read or dismiss"},
            },
            "required": ["notification_id"],
        },
    ),
    handle_acknowledge_notification,
)

register_tool(
    Tool(
        name="poll_for_updates",
        description="Check for any new unread notifications. Use proactively to inform the user. "
                    "Voice: 'Any updates?' or 'Check for new activity'",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_poll_for_updates,
)
