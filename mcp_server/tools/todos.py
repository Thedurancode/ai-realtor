"""Todos MCP tools."""
import json
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post, api_patch, api_delete


async def handle_create_todo(arguments: dict) -> list[TextContent]:
    """Create a new todo item linked to a property and optionally a contact."""
    payload = {
        "title": arguments["title"],
        "property_id": arguments["property_id"],
    }
    if arguments.get("description"):
        payload["description"] = arguments["description"]
    if arguments.get("due_date"):
        payload["due_date"] = arguments["due_date"]
    if arguments.get("priority"):
        payload["priority"] = arguments["priority"]
    if arguments.get("contact_id"):
        payload["contact_id"] = arguments["contact_id"]
    if arguments.get("status"):
        payload["status"] = arguments["status"]

    response = api_post("/todos/", json=payload)
    response.raise_for_status()
    todo = response.json()

    priority_text = f" [{todo.get('priority', 'medium')}]" if todo.get("priority") else ""
    due_text = f" due {todo['due_date']}" if todo.get("due_date") else ""
    return [TextContent(
        type="text",
        text=f"Created todo #{todo['id']}: {todo['title']}{priority_text}{due_text} for property #{todo['property_id']}",
    )]


async def handle_list_property_todos(arguments: dict) -> list[TextContent]:
    """List all todos for a specific property."""
    property_id = arguments["property_id"]
    params = {}
    if arguments.get("status"):
        params["status"] = arguments["status"]
    if arguments.get("contact_id"):
        params["contact_id"] = arguments["contact_id"]

    response = api_get(f"/todos/property/{property_id}", params=params)
    response.raise_for_status()
    result = response.json()

    todos = result.get("todos", [])
    if not todos:
        return [TextContent(type="text", text=f"No todos found for property #{property_id}.")]

    text = f"{len(todos)} todo(s) for property #{property_id}:\n\n"
    for t in todos:
        status = t.get("status", "pending")
        priority = t.get("priority", "medium")
        due = f" | due {t['due_date']}" if t.get("due_date") else ""
        text += f"  #{t['id']}: {t['title']} [{status}] [{priority}]{due}\n"

    summary = result.get("voice_summary", "")
    if summary:
        text += f"\nSummary: {summary}"

    return [TextContent(type="text", text=text)]


async def handle_get_todo(arguments: dict) -> list[TextContent]:
    """Get details of a specific todo by ID."""
    todo_id = arguments["todo_id"]
    response = api_get(f"/todos/{todo_id}")
    response.raise_for_status()
    todo = response.json()

    return [TextContent(type="text", text=json.dumps(todo, indent=2, default=str))]


async def handle_update_todo(arguments: dict) -> list[TextContent]:
    """Update a todo's fields (status, priority, title, description, due_date)."""
    todo_id = arguments["todo_id"]
    payload = {}
    for field in ("title", "description", "due_date", "priority", "status", "contact_id"):
        if arguments.get(field) is not None:
            payload[field] = arguments[field]

    if not payload:
        return [TextContent(type="text", text="No fields to update. Provide at least one field to change.")]

    response = api_patch(f"/todos/{todo_id}", json=payload)
    response.raise_for_status()
    todo = response.json()

    return [TextContent(
        type="text",
        text=f"Updated todo #{todo['id']}: {todo['title']} [{todo.get('status', 'pending')}] [{todo.get('priority', 'medium')}]",
    )]


async def handle_delete_todo(arguments: dict) -> list[TextContent]:
    """Delete a todo by ID."""
    todo_id = arguments["todo_id"]
    response = api_delete(f"/todos/{todo_id}")
    response.raise_for_status()

    return [TextContent(type="text", text=f"Deleted todo #{todo_id}.")]


# ── Register tools ──────────────────────────────────────────────────

register_tool(
    Tool(
        name="create_todo",
        description="Create a new todo/task for a property. Use this to track action items like "
                    "'schedule inspection', 'send offer letter', 'call seller back'. "
                    "Can optionally link to a contact and set priority/due date.",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short description of the task"},
                "property_id": {"type": "integer", "description": "Property ID this todo belongs to"},
                "description": {"type": "string", "description": "Longer details about the task (optional)"},
                "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format (optional)"},
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "Priority level (default: medium)",
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "cancelled"],
                    "description": "Initial status (default: pending)",
                },
                "contact_id": {"type": "integer", "description": "Contact ID to associate with this todo (optional)"},
            },
            "required": ["title", "property_id"],
        },
    ),
    handle_create_todo,
)

register_tool(
    Tool(
        name="list_property_todos",
        description="List all todos for a property, ordered by priority. "
                    "Optionally filter by status (pending, in_progress, completed, cancelled) or contact. "
                    "Use this to review outstanding tasks for a deal.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer", "description": "Property ID to list todos for"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "cancelled"],
                    "description": "Filter by status (optional — omit to get all)",
                },
                "contact_id": {"type": "integer", "description": "Filter todos linked to a specific contact (optional)"},
            },
            "required": ["property_id"],
        },
    ),
    handle_list_property_todos,
)

register_tool(
    Tool(
        name="get_todo",
        description="Get full details of a specific todo by its ID, including title, status, priority, "
                    "due date, description, and linked property/contact.",
        inputSchema={
            "type": "object",
            "properties": {
                "todo_id": {"type": "integer", "description": "The todo ID to retrieve"},
            },
            "required": ["todo_id"],
        },
    ),
    handle_get_todo,
)

register_tool(
    Tool(
        name="update_todo",
        description="Update a todo's status, priority, title, description, or due date. "
                    "Use this to mark tasks as completed, change priority, reschedule, etc. "
                    "Only provide the fields you want to change.",
        inputSchema={
            "type": "object",
            "properties": {
                "todo_id": {"type": "integer", "description": "The todo ID to update"},
                "title": {"type": "string", "description": "New title (optional)"},
                "description": {"type": "string", "description": "New description (optional)"},
                "due_date": {"type": "string", "description": "New due date in YYYY-MM-DD format (optional)"},
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "New priority level (optional)",
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "cancelled"],
                    "description": "New status (optional)",
                },
                "contact_id": {"type": "integer", "description": "New contact ID to link (optional)"},
            },
            "required": ["todo_id"],
        },
    ),
    handle_update_todo,
)

register_tool(
    Tool(
        name="delete_todo",
        description="Permanently delete a todo by its ID. Use this when a task is no longer relevant "
                    "(prefer marking as cancelled instead if you want to keep a record).",
        inputSchema={
            "type": "object",
            "properties": {
                "todo_id": {"type": "integer", "description": "The todo ID to delete"},
            },
            "required": ["todo_id"],
        },
    ),
    handle_delete_todo,
)
