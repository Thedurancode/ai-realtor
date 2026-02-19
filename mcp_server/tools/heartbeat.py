"""Property heartbeat MCP tool — pipeline stage, checklist, and health at a glance."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get
from ..utils.property_resolver import resolve_property_id


async def handle_get_property_heartbeat(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)

    response = api_get(f"/properties/{property_id}/heartbeat")
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "")

    stage = data.get("stage_label", "Unknown")
    health = data.get("health", "unknown")
    health_tag = {"healthy": "OK", "stale": "STALE", "blocked": "BLOCKED"}.get(health, "?")
    days_in = data.get("days_in_stage", 0)
    threshold = data.get("stale_threshold_days", 0)

    text = f"{voice}\n\n"
    text += f"Stage: {stage} ({data.get('stage_index', 0) + 1} of {data.get('total_stages', 5)})\n"
    text += f"Health: {health_tag}"
    if data.get("health_reason"):
        text += f" — {data['health_reason']}"
    text += f"\nTime in stage: {days_in:.1f} days (threshold: {threshold})\n"

    text += "\nChecklist:\n"
    for item in data.get("checklist", []):
        mark = "[x]" if item["done"] else "[ ]"
        line = f"  {mark} {item['label']}"
        if item.get("detail"):
            line += f" ({item['detail']})"
        text += line + "\n"

    text += f"\nNext step: {data.get('next_action', 'N/A')}"

    if data.get("deal_score") is not None:
        text += f"\nDeal score: {data['deal_score']:.0f}/100 (Grade {data.get('score_grade', '?')})"

    return [TextContent(type="text", text=text.strip())]


register_tool(
    Tool(
        name="get_property_heartbeat",
        description=(
            "Get the pipeline heartbeat for a property — shows current stage, "
            "done/pending checklist, health status (healthy/stale/blocked), "
            "time in stage, and next recommended action. "
            "Voice: 'What's the heartbeat on property 5?', "
            "'How is property 3 doing?', 'Is property 5 stuck?', "
            "'Check the pulse on the Hillsborough property'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "The property ID (optional if address provided)",
                },
                "address": {
                    "type": "string",
                    "description": "Property address (voice-friendly)",
                },
            },
        },
    ),
    handle_get_property_heartbeat,
)
