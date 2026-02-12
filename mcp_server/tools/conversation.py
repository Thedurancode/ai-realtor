"""Conversation history MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post, api_delete


SESSION_ID = "mcp_session"


async def handle_get_conversation_history(arguments: dict) -> list[TextContent]:
    """Get recent conversation history."""
    limit = arguments.get("limit", 10)
    hours_ago = arguments.get("hours_ago")

    params = {"session_id": SESSION_ID, "limit": limit}
    if hours_ago:
        params["hours_ago"] = hours_ago

    response = api_get("/context/history", params=params)
    response.raise_for_status()
    data = response.json()

    return [TextContent(type="text", text=data["summary"])]


async def handle_what_did_we_discuss(arguments: dict) -> list[TextContent]:
    """Natural language version - what did we talk about."""
    response = api_get("/context/history", params={"session_id": SESSION_ID, "limit": 5})
    response.raise_for_status()
    data = response.json()

    if data["count"] == 0:
        return [TextContent(type="text", text="We haven't discussed anything yet in this session.")]

    return [TextContent(type="text", text=data["summary"])]


async def handle_clear_conversation_history(arguments: dict) -> list[TextContent]:
    """Clear conversation history."""
    response = api_delete("/context/history", params={"session_id": SESSION_ID})
    response.raise_for_status()
    data = response.json()

    return [TextContent(type="text", text=f"Cleared {data['deleted']} conversation entries.")]


def log_tool_call(tool_name: str, input_summary: str, output_summary: str, success: bool = True, duration_ms: int = None):
    """Helper to log a tool call to conversation history."""
    try:
        api_post("/context/history/log", json={
            "session_id": SESSION_ID,
            "tool_name": tool_name,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "success": success,
            "duration_ms": duration_ms,
        })
    except Exception:
        pass  # Don't fail the main operation if logging fails


# ── Tool Registration ──

register_tool(
    Tool(
        name="get_conversation_history",
        description="Get recent conversation history. Shows what we've discussed, what tools were used, and the results. Use this when the user asks 'what did we talk about?' or 'what was that property again?'",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "number",
                    "description": "Number of recent entries to return (default: 10)",
                    "default": 10
                },
                "hours_ago": {
                    "type": "number",
                    "description": "Only show entries from the last N hours"
                }
            }
        }
    ),
    handle_get_conversation_history
)

register_tool(
    Tool(
        name="what_did_we_discuss",
        description="Natural language tool for 'what did we talk about?', 'remind me what we discussed', 'what was that address?'. Returns a summary of recent conversation.",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    handle_what_did_we_discuss
)

register_tool(
    Tool(
        name="clear_conversation_history",
        description="Clear the conversation history. Use when user says 'forget what we talked about' or 'start fresh'.",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    handle_clear_conversation_history
)
