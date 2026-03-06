"""Morning Brief MCP tool — trigger the daily morning summary via Telegram."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_post


async def handle_trigger_daily_brief(arguments: dict) -> list[TextContent]:
    """Send the daily morning brief via Telegram."""
    resp = api_post("/morning-brief/send")
    resp.raise_for_status()
    data = resp.json()

    brief = data.get("brief", "Brief generated.")
    sent = data.get("sent", False)
    status = "Sent via Telegram" if sent else "Generated but Telegram send failed (check credentials)"

    text = f"{brief}\n\n---\nStatus: {status}"
    return [TextContent(type="text", text=text)]


register_tool(
    Tool(
        name="trigger_daily_brief",
        description="Send the daily morning brief via Telegram. Includes follow-ups due today, new leads, pipeline summary, closings, and scheduled tasks. "
                    "Voice: 'Send my morning brief' or 'Daily briefing' or 'Morning summary to Telegram'",
        inputSchema={"type": "object", "properties": {}},
    ),
    handle_trigger_daily_brief,
)
