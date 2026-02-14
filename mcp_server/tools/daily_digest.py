"""Daily digest MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_get_daily_digest(arguments: dict) -> list[TextContent]:
    """Get the latest daily digest."""
    resp = api_get("/digest/latest")
    resp.raise_for_status()
    data = resp.json()

    if "message" in data and "No digest" in data["message"]:
        return [TextContent(type="text", text="No daily digest has been generated yet. Say 'generate a digest' to create one.")]

    text = ""
    if data.get("digest_text"):
        text += data["digest_text"] + "\n\n"

    highlights = data.get("key_highlights", [])
    if highlights:
        text += "Key highlights:\n"
        for h in highlights:
            text += f"  - {h}\n"
        text += "\n"

    urgent = data.get("urgent_actions", [])
    if urgent:
        text += "Urgent actions:\n"
        for a in urgent:
            text += f"  - {a}\n"
        text += "\n"

    if data.get("created_at"):
        text += f"Generated: {data['created_at']}"

    return [TextContent(type="text", text=text.strip() or "Digest is empty.")]


async def handle_trigger_daily_digest(arguments: dict) -> list[TextContent]:
    """Generate a fresh daily digest."""
    resp = api_post("/digest/generate")
    resp.raise_for_status()
    data = resp.json()

    voice = data.get("voice_summary", "Digest generated.")
    highlights = data.get("key_highlights", [])

    text = f"Fresh digest generated!\n\n{voice}\n\n"
    if highlights:
        text += "Highlights:\n"
        for h in highlights:
            text += f"  - {h}\n"

    return [TextContent(type="text", text=text.strip())]


register_tool(
    Tool(
        name="get_daily_digest",
        description="Get the latest daily digest — an AI-generated morning briefing combining portfolio stats, alerts, contract status, and recommendations. "
                    "Voice: 'What\\'s my daily digest?' or 'Morning summary' or 'What happened overnight?'",
        inputSchema={"type": "object", "properties": {}},
    ),
    handle_get_daily_digest,
)

register_tool(
    Tool(
        name="trigger_daily_digest",
        description="Generate a fresh daily digest right now. Uses AI to analyze your portfolio, alerts, contracts, and activity. "
                    "Voice: 'Generate a digest' or 'Give me a fresh briefing'",
        inputSchema={"type": "object", "properties": {}},
    ),
    handle_trigger_daily_digest,
)
