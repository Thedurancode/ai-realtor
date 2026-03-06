"""Voice agent MCP tools — start calls, list calls, get transcripts."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


# ── Handlers ──

async def handle_start_voice_call(arguments: dict) -> list[TextContent]:
    payload = {"phone_number": arguments["phone_number"]}
    response = api_post("/voice/agent/call", json=payload)
    response.raise_for_status()
    result = response.json()

    output = (
        f"Voice agent call initiated to {result.get('phone_number', 'N/A')}. "
        f"Call ID: {result.get('call_id', 'N/A')}, status: {result.get('status', 'N/A')}."
    )
    return [TextContent(type="text", text=output)]


async def handle_list_voice_calls(arguments: dict) -> list[TextContent]:
    params = {}
    if arguments.get("limit"):
        params["limit"] = arguments["limit"]
    response = api_get("/voice/agent/calls", params=params)
    response.raise_for_status()
    calls = response.json()

    if not calls:
        return [TextContent(type="text", text="No voice agent calls found.")]

    lines = [f"Found {len(calls)} voice agent call(s):"]
    for c in calls:
        direction = c.get("direction", "?")
        status = c.get("status", "?")
        phone = c.get("phone_number", "?")
        started = c.get("started_at", "?")
        lines.append(f"  - {c.get('call_id', '?')} | {direction} | {phone} | {status} | {started}")

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_get_voice_call(arguments: dict) -> list[TextContent]:
    call_id = arguments["call_id"]
    response = api_get(f"/voice/agent/calls/{call_id}")
    response.raise_for_status()
    result = response.json()

    output = (
        f"Call {result.get('call_id', 'N/A')} ({result.get('direction', '?')}) — "
        f"status: {result.get('status', '?')}, phone: {result.get('phone_number', '?')}\n"
    )

    transcript = result.get("transcript", "")
    if transcript:
        # Truncate long transcripts
        if len(transcript) > 2000:
            transcript = transcript[:2000] + "... (truncated)"
        output += f"\nTranscript:\n{transcript}\n"
    else:
        output += "\nNo transcript available.\n"

    actions = result.get("actions_taken", [])
    if actions:
        output += f"\nActions taken ({len(actions)}):\n"
        for a in actions:
            output += f"  - {a.get('tool', '?')}({a.get('arguments', {})})\n"

    return [TextContent(type="text", text=output)]


# ── Tool Registration ──

register_tool(
    Tool(
        name="start_voice_call",
        description=(
            "Initiate an outbound voice agent call. The AI assistant will call the "
            "given phone number and can execute property management tools by voice. "
            "Phone number must be in E.164 format (e.g., +14155551234)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number in E.164 format (e.g., +14155551234)",
                },
            },
            "required": ["phone_number"],
        },
    ),
    handle_start_voice_call,
)

register_tool(
    Tool(
        name="list_voice_calls",
        description="List recent voice agent calls with status and timestamps.",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max number of calls to return (default 20)",
                },
            },
        },
    ),
    handle_list_voice_calls,
)

register_tool(
    Tool(
        name="get_voice_call",
        description="Get the full transcript and actions taken during a voice agent call.",
        inputSchema={
            "type": "object",
            "properties": {
                "call_id": {
                    "type": "string",
                    "description": "The call ID to retrieve",
                },
            },
            "required": ["call_id"],
        },
    ),
    handle_get_voice_call,
)
