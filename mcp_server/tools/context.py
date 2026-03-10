"""Conversation Context — Manage conversation history and context for the AI assistant."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_delete


async def handle_get_context_summary(arguments: dict) -> list[TextContent]:
    """Get a summary of the current conversation context."""
    response = api_get("/context/summary")
    response.raise_for_status()
    data = response.json()

    text = "**Conversation Context Summary**\n\n"

    if data.get("total_messages"):
        text += f"Total messages: {data['total_messages']}\n"

    if data.get("topics"):
        text += "\n**Topics Discussed:**\n"
        for topic in data["topics"]:
            text += f"- {topic}\n"

    if data.get("properties_mentioned"):
        text += "\n**Properties Mentioned:**\n"
        for prop in data["properties_mentioned"]:
            text += f"- {prop}\n"

    if data.get("contacts_mentioned"):
        text += "\n**Contacts Mentioned:**\n"
        for contact in data["contacts_mentioned"]:
            text += f"- {contact}\n"

    if data.get("action_items"):
        text += "\n**Pending Action Items:**\n"
        for item in data["action_items"]:
            text += f"- {item}\n"

    if data.get("session_start"):
        text += f"\nSession started: {data['session_start']}\n"

    if not data.get("total_messages") and not data.get("topics"):
        text += "No active conversation context. Start a conversation to build context."

    return [TextContent(type="text", text=text)]


async def handle_clear_context(arguments: dict) -> list[TextContent]:
    """Clear the current conversation context."""
    response = api_delete("/context/clear")
    response.raise_for_status()
    data = response.json()

    text = "**Conversation Context Cleared**\n\n"
    text += data.get("message", "Context has been reset. Starting fresh.")

    return [TextContent(type="text", text=text)]


async def handle_get_history(arguments: dict) -> list[TextContent]:
    """Get conversation history."""
    params = {}
    if arguments.get("limit"):
        params["limit"] = arguments["limit"]
    if arguments.get("offset"):
        params["offset"] = arguments["offset"]

    response = api_get("/context/history", params=params)
    response.raise_for_status()
    data = response.json()

    messages = data.get("messages", [])
    total = data.get("total", len(messages))

    text = f"**Conversation History** ({len(messages)} of {total} messages)\n\n"

    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")

        # Truncate long messages for readability
        if len(content) > 200:
            content = content[:200] + "..."

        if timestamp:
            text += f"[{timestamp}] **{role}:** {content}\n\n"
        else:
            text += f"**{role}:** {content}\n\n"

    if not messages:
        text += "No conversation history available."

    return [TextContent(type="text", text=text)]


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

    text = f"**Property Conversation History**\n\n"

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
        timestamp = msg.get("timestamp", "")

        if len(content) > 200:
            content = content[:200] + "..."

        if timestamp:
            text += f"[{timestamp}] **{role}:** {content}\n\n"
        else:
            text += f"**{role}:** {content}\n\n"

    if not messages:
        text += "No conversation history found for this property."

    return [TextContent(type="text", text=text)]


async def handle_clear_history(arguments: dict) -> list[TextContent]:
    """Clear all conversation history."""
    response = api_delete("/context/history")
    response.raise_for_status()
    data = response.json()

    text = "**Conversation History Cleared**\n\n"
    text += data.get("message", "All conversation history has been deleted.")

    return [TextContent(type="text", text=text)]


# ── Registration ──

register_tool(
    Tool(
        name="get_conversation_history",
        description=(
            "Get the conversation history showing previous messages and interactions. "
            "Useful for reviewing what was discussed earlier in the session. "
            "Voice: 'Show me our conversation history', 'What did we talk about?', "
            "'Show previous messages', 'What was discussed earlier?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "number",
                    "description": "Maximum number of messages to return (default: all)",
                },
                "offset": {
                    "type": "number",
                    "description": "Number of messages to skip from the start",
                },
            },
        },
    ),
    handle_get_history,
)

register_tool(
    Tool(
        name="what_did_we_discuss",
        description=(
            "Get a summary of the current conversation context including topics discussed, "
            "properties and contacts mentioned, and pending action items. "
            "Voice: 'What did we discuss?', 'Summarize our conversation', "
            "'What have we been talking about?', 'Give me a context summary'"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_get_context_summary,
)

register_tool(
    Tool(
        name="clear_conversation_history",
        description=(
            "Clear the current conversation context and start fresh. "
            "Removes all tracked topics, mentions, and action items from the session. "
            "Voice: 'Clear the conversation', 'Start fresh', 'Reset our chat context', "
            "'Forget what we discussed'"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_clear_context,
)

register_tool(
    Tool(
        name="get_property_conversation_history",
        description=(
            "Get all conversation history related to a specific property by its ID. "
            "Shows every message where the property was discussed, including actions taken. "
            "Voice: 'What did we discuss about property 5?', 'Show history for 123 Main St', "
            "'What have we said about this property?', 'Property conversation log for ID 42'"
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
            "This is a destructive action that cannot be undone. "
            "Voice: 'Delete all conversation history', 'Wipe all chat logs', "
            "'Clear everything we've ever discussed'"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_clear_history,
)
