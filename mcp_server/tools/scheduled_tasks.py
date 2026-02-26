"""Scheduled tasks MCP tools — voice-created reminders and automation."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post, api_delete
from ..utils.property_resolver import find_property_by_address


async def handle_create_scheduled_task(arguments: dict) -> list[TextContent]:
    """Create a scheduled reminder or recurring task."""
    title = arguments.get("title")
    if not title:
        return [TextContent(type="text", text="Please provide a title for the task.")]

    scheduled_at = arguments.get("scheduled_at")
    if not scheduled_at:
        return [TextContent(type="text", text="Please provide when to schedule this (scheduled_at in ISO format, e.g. '2026-02-15T10:00:00Z').")]

    # Resolve property if address provided
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    if address and not property_id:
        try:
            property_id = find_property_by_address(address)
        except ValueError:
            # If address doesn't resolve, still create the task (property is optional)
            pass

    payload = {
        "title": title,
        "scheduled_at": scheduled_at,
        "task_type": arguments.get("task_type", "reminder"),
        "description": arguments.get("description"),
        "property_id": property_id,
        "repeat_interval_hours": arguments.get("repeat_interval_hours"),
        "created_by": "voice",
    }
    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}

    response = api_post("/scheduled-tasks/", json=payload)
    response.raise_for_status()
    data = response.json()

    text = f"Scheduled task created (#{data['id']}): '{data['title']}' at {data['scheduled_at']}."
    if data.get("repeat_interval_hours"):
        text += f" Repeats every {data['repeat_interval_hours']} hours."
    if data.get("property_id"):
        text += f" Linked to property #{data['property_id']}."

    return [TextContent(type="text", text=text)]


async def handle_list_scheduled_tasks(arguments: dict) -> list[TextContent]:
    """List scheduled tasks/reminders."""
    params = {}
    status = arguments.get("status")
    if status:
        params["status"] = status
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    if address and not property_id:
        try:
            property_id = find_property_by_address(address)
        except ValueError:
            pass
    if property_id:
        params["property_id"] = property_id

    response = api_get("/scheduled-tasks/", params=params)
    response.raise_for_status()
    tasks = response.json()

    if not tasks:
        return [TextContent(type="text", text="No scheduled tasks found.")]

    text = f"You have {len(tasks)} scheduled task(s).\n\n"
    for t in tasks:
        line = f"#{t['id']} {t['title']} — {t['status']}, scheduled {t['scheduled_at']}"
        if t.get("property_id"):
            line += f", property #{t['property_id']}"
        if t.get("repeat_interval_hours"):
            line += f", repeats every {t['repeat_interval_hours']}h"
        text += line + "\n"

    return [TextContent(type="text", text=text.strip())]


async def handle_cancel_scheduled_task(arguments: dict) -> list[TextContent]:
    """Cancel a scheduled task."""
    task_id = arguments.get("task_id")
    if not task_id:
        return [TextContent(type="text", text="Please provide a task_id to cancel.")]

    response = api_delete(f"/scheduled-tasks/{task_id}")
    response.raise_for_status()
    data = response.json()

    return [TextContent(type="text", text=f"Task #{data['id']} '{data['title']}' has been cancelled.")]


# ── Registration ──

register_tool(
    Tool(
        name="create_scheduled_task",
        description=(
            "Create a scheduled reminder or recurring task. Use for voice commands like "
            "'Remind me to follow up on the Brooklyn property in 2 days', "
            "'Schedule a compliance check for Friday', "
            "'Set a daily reminder to check contracts'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title (e.g., 'Follow up on 123 Main St')",
                },
                "scheduled_at": {
                    "type": "string",
                    "description": "When to execute (ISO 8601, e.g., '2026-02-15T10:00:00Z')",
                },
                "task_type": {
                    "type": "string",
                    "enum": ["reminder", "recurring", "follow_up", "contract_check"],
                    "default": "reminder",
                    "description": "Type of scheduled task",
                },
                "description": {
                    "type": "string",
                    "description": "Optional detailed description",
                },
                "property_id": {
                    "type": "number",
                    "description": "Optional property ID to link this task to (optional if address provided)",
                },
                "address": {
                    "type": "string",
                    "description": "Property address to search for (voice-friendly, e.g., '123 Main Street' or 'the Brooklyn property')",
                },
                "repeat_interval_hours": {
                    "type": "number",
                    "description": "For recurring tasks: repeat every N hours",
                },
            },
            "required": ["title", "scheduled_at"],
        },
    ),
    handle_create_scheduled_task,
)

register_tool(
    Tool(
        name="list_scheduled_tasks",
        description=(
            "List scheduled tasks and reminders. Voice: 'What reminders do I have?', "
            "'Show my scheduled tasks', 'Any upcoming reminders?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "completed", "cancelled", "failed"],
                    "description": "Filter by status (default: all)",
                },
                "property_id": {
                    "type": "number",
                    "description": "Filter by property ID (optional if address provided)",
                },
                "address": {
                    "type": "string",
                    "description": "Property address to filter by (voice-friendly, e.g., '123 Main Street' or 'the Brooklyn property')",
                },
            },
        },
    ),
    handle_list_scheduled_tasks,
)

register_tool(
    Tool(
        name="cancel_scheduled_task",
        description=(
            "Cancel a scheduled task or reminder. Voice: 'Cancel reminder 5', "
            "'Remove the follow-up for property 3'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "number",
                    "description": "The scheduled task ID to cancel",
                },
            },
            "required": ["task_id"],
        },
    ),
    handle_cancel_scheduled_task,
)
