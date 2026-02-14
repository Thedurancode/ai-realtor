"""Pipeline automation MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_get_pipeline_status(arguments: dict) -> list[TextContent]:
    """Get recent pipeline auto-transitions."""
    resp = api_get("/pipeline/status")
    resp.raise_for_status()
    data = resp.json()

    transitions = data.get("recent_transitions", [])
    total = data.get("total_recent", 0)

    if not transitions:
        return [TextContent(type="text", text="No recent pipeline auto-transitions. All properties are stable.")]

    text = f"Pipeline automation: {total} recent transition(s):\n\n"
    for t in transitions:
        text += f"  Property #{t['property_id']}: {t['title']}\n"
        text += f"    {t['message']}\n"
        text += f"    Time: {t.get('created_at', 'unknown')}\n\n"

    return [TextContent(type="text", text=text)]


async def handle_trigger_pipeline_check(arguments: dict) -> list[TextContent]:
    """Manually trigger pipeline automation check."""
    resp = api_post("/pipeline/check")
    resp.raise_for_status()
    data = resp.json()

    checked = data.get("checked", 0)
    transitioned = data.get("transitioned", 0)
    transitions = data.get("transitions", [])

    if transitioned == 0:
        return [TextContent(type="text", text=f"Pipeline check complete. Checked {checked} properties — no transitions needed.")]

    text = f"Pipeline check complete. Checked {checked} properties, {transitioned} transitioned:\n\n"
    for t in transitions:
        text += f"  Property #{t['property_id']} ({t['address']}): {t['from_status']} → {t['to_status']}\n"
        text += f"    Reason: {t['reason']}\n\n"

    return [TextContent(type="text", text=text)]


register_tool(
    Tool(
        name="get_pipeline_status",
        description="Get recent pipeline automation transitions. Shows which properties were auto-advanced. "
                    "Voice: 'What\\'s the pipeline status?' or 'Show recent auto-transitions'",
        inputSchema={"type": "object", "properties": {}},
    ),
    handle_get_pipeline_status,
)

register_tool(
    Tool(
        name="trigger_pipeline_check",
        description="Manually trigger pipeline automation to check all properties for auto-transitions. "
                    "Voice: 'Run pipeline automation now' or 'Check for auto-transitions'",
        inputSchema={"type": "object", "properties": {}},
    ),
    handle_trigger_pipeline_check,
)
