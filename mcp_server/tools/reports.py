"""PDF report MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_post
from ..utils.property_resolver import resolve_property_id


async def send_property_report(property_id: int, report_type: str = "property_overview") -> dict:
    response = api_post(
        f"/property-recap/property/{property_id}/send-report",
        params={"report_type": report_type},
    )
    response.raise_for_status()
    return response.json()


async def handle_send_property_report(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    report_type = arguments.get("report_type", "property_overview")
    result = await send_property_report(property_id=property_id, report_type=report_type)

    text = f"REPORT SENT SUCCESSFULLY\n\n"
    text += f"Report: {result.get('report_type', report_type).replace('_', ' ').title()}\n"
    text += f"Property: {result.get('property_address', 'N/A')}\n"
    text += f"File: {result.get('filename', 'N/A')}\n"
    text += f"Sent to: {result.get('message', 'agent email')}\n\n"

    available = result.get("available_report_types", [])
    if available:
        text += "Available report types:\n"
        for rt in available:
            text += f"  - {rt['type']}: {rt['name']}\n"

    return [TextContent(type="text", text=text)]


register_tool(
    Tool(
        name="send_property_report",
        description=(
            "SEND PDF REPORT: Generate a professional PDF report for a property "
            "and email it to you. Voice-friendly: say the address instead of the ID. "
            "Example: 'Send me the property overview for 123 Main Street'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "Property ID (optional if address provided)",
                },
                "address": {
                    "type": "string",
                    "description": "Property address to search for (voice-friendly)",
                },
                "report_type": {
                    "type": "string",
                    "description": "Type of report to generate. Default: property_overview",
                    "default": "property_overview",
                    "enum": ["property_overview"],
                },
            },
        },
    ),
    handle_send_property_report,
)
