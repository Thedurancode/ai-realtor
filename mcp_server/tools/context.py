"""Context tools — supplements conversation.py with property-specific history and full clear."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_delete


async def handle_get_property_history(arguments: dict) -> list[TextContent]:
    """Get conversation history related to a specific property."""
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Error: property_id is required.")]

    response = api_get(f"/context/history/property/{property_id}")
    response.raise_for_status()
    data = response.json()

    messages = data.get("messages", [])
    property_info = data.get("property", {})

    text = "**Property Conversation History**\n\n"
    if property_info.get("address"):
        text += f"Property: {property_info['address']}"
        if property_info.get("city"):
            text += f", {property_info['city']}"
        text += "\n"

    text += f"Property ID: {property_id}\n"
    text += f"Related messages: {len(messages)}\n\n"

    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        if len(content) > 200:
            content = content[:200] + "..."
        timestamp = msg.get("timestamp", "")
        if timestamp:
            text += f"[{timestamp}] **{role}:** {content}\n\n"
        else:
            text += f"**{role}:** {content}\n\n"

    if not messages:
        text += "No conversation history found for this property."

    return [TextContent(type="text", text=text)]


async def handle_clear_all_history(arguments: dict) -> list[TextContent]:
    """Clear all conversation history permanently."""
    response = api_delete("/context/history")
    response.raise_for_status()
    data = response.json()
    return [TextContent(type="text", text=data.get("message", "All conversation history has been deleted."))]


# ── Registration ──

register_tool(
    Tool(
        name="get_property_conversation_history",
        description=(
            "Get all conversation history related to a specific property by its ID. "
            "Voice: 'What did we discuss about property 5?', 'Show history for 123 Main St'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "The property ID to get conversation history for",
                },
            },
            "required": ["property_id"],
        },
    ),
    handle_get_property_history,
)

register_tool(
    Tool(
        name="clear_all_history",
        description=(
            "Permanently clear ALL conversation history across all sessions. "
            "Voice: 'Delete all conversation history', 'Wipe all chat logs'"
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    handle_clear_all_history,
)
