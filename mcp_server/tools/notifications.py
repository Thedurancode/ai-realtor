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

    if isinstance(result, list) and len(result) > 0:
        summary = f"Found {len(result)} notification(s):\n\n"
        for notif in result:
            summary += f"{notif.get('icon', '\U0001f514')} {notif['title']}\n"
            summary += f"   {notif['message']}\n"
            summary += f"   Type: {notif['type']} | Priority: {notif['priority']}\n"
            summary += f"   Created: {notif['created_at']}\n\n"
        return [TextContent(type="text", text=summary)]
    else:
        return [TextContent(type="text", text="No notifications found.")]


# ── Tool Registration ──

register_tool(
    Tool(name="send_notification", description="Send a custom notification to the TV display. Use this to alert about important events, milestones, or custom messages. The notification will appear as an animated toast on the TV display.", inputSchema={"type": "object", "properties": {"title": {"type": "string", "description": "Notification title (concise, under 50 chars)"}, "message": {"type": "string", "description": "Notification message"}, "notification_type": {"type": "string", "description": "Type of notification", "enum": ["general", "contract_signed", "new_lead", "property_price_change", "property_status_change", "appointment_reminder", "skip_trace_complete", "enrichment_complete"], "default": "general"}, "priority": {"type": "string", "description": "Priority level (affects color)", "enum": ["low", "medium", "high", "urgent"], "default": "medium"}, "icon": {"type": "string", "description": "Emoji icon to display (e.g., \U0001f389, \u26a0\ufe0f, \U0001f4dd)", "default": "\U0001f514"}, "property_id": {"type": "number", "description": "Optional property ID to associate"}, "auto_dismiss_seconds": {"type": "number", "description": "Auto-dismiss after X seconds (5-30, default: 10)", "default": 10}}, "required": ["title", "message"]}),
    handle_send_notification
)

register_tool(
    Tool(name="list_notifications", description="List recent notifications from the system. Shows notification history including contracts signed, new leads, price changes, etc.", inputSchema={"type": "object", "properties": {"limit": {"type": "number", "description": "Number of notifications to return (default: 10)", "default": 10}, "unread_only": {"type": "boolean", "description": "Only show unread notifications", "default": False}}}),
    handle_list_notifications
)
