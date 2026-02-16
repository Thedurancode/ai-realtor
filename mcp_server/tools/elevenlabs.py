"""ElevenLabs voice agent MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


# ── Handlers ──

async def handle_elevenlabs_setup(arguments: dict) -> list[TextContent]:
    response = api_post("/elevenlabs/setup")
    response.raise_for_status()
    result = response.json()

    agent_info = result.get("agent", {})
    mcp_info = result.get("mcp_server", {})

    output = f"ElevenLabs voice agent set up. Agent ID: {agent_info.get('agent_id', 'N/A')}, LLM: {agent_info.get('llm', 'N/A')}, status: {agent_info.get('status', 'N/A')}."
    output += f" MCP server: {mcp_info.get('url', 'N/A')}. The agent now has access to all property management tools via MCP."
    return [TextContent(type="text", text=output)]


async def handle_elevenlabs_call(arguments: dict) -> list[TextContent]:
    payload = {"phone_number": arguments["phone_number"]}
    if arguments.get("custom_first_message"):
        payload["custom_first_message"] = arguments["custom_first_message"]

    response = api_post("/elevenlabs/call", json=payload)
    response.raise_for_status()
    result = response.json()

    output = f"ElevenLabs call initiated to {result.get('to_number', 'N/A')}. Call ID: {result.get('call_id', 'N/A')}, status: {result.get('status', 'N/A')}."
    return [TextContent(type="text", text=output)]


async def handle_elevenlabs_status(arguments: dict) -> list[TextContent]:
    response = api_get("/elevenlabs/agent")
    response.raise_for_status()
    result = response.json()

    if result.get("error"):
        return [TextContent(type="text", text=f"Warning: {result['error']}")]

    output = f"ElevenLabs agent \"{result.get('name', 'N/A')}\" — status: {result.get('status', 'N/A')}. Agent ID: {result.get('agent_id', 'N/A')}, MCP URL: {result.get('mcp_sse_url', 'N/A')}."
    return [TextContent(type="text", text=output)]


# ── Tool Registration ──

register_tool(
    Tool(name="elevenlabs_setup", description="Set up the ElevenLabs voice agent. Registers the MCP SSE server and creates an AI agent that can use all property management tools during voice calls. One-time setup.", inputSchema={"type": "object", "properties": {}}),
    handle_elevenlabs_setup
)

register_tool(
    Tool(name="elevenlabs_call", description="Make an outbound phone call using the ElevenLabs voice agent. The agent can use all property tools during the call. Example: 'Call +14155551234 using ElevenLabs'.", inputSchema={"type": "object", "properties": {"phone_number": {"type": "string", "description": "Phone number in E.164 format (e.g., +14155551234)"}, "custom_first_message": {"type": "string", "description": "Optional custom greeting for the call"}}, "required": ["phone_number"]}),
    handle_elevenlabs_call
)

register_tool(
    Tool(name="elevenlabs_status", description="Get the ElevenLabs voice agent status and configuration. Shows agent ID, MCP connection, and widget embed code.", inputSchema={"type": "object", "properties": {}}),
    handle_elevenlabs_status
)
