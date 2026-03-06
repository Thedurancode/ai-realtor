"""CMA (Comparative Market Analysis) Report MCP tools."""

import json
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_post, api_get
from ..utils.property_resolver import resolve_property_id


# ── Handlers ──

async def handle_generate_cma_report(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    agent_brand_id = arguments.get("agent_brand_id")

    payload = {"property_id": property_id}
    if agent_brand_id:
        payload["agent_brand_id"] = agent_brand_id

    response = api_post("/cma/generate", json=payload)
    response.raise_for_status()

    # The response is a PDF binary — we can't return it directly via MCP text,
    # so confirm it was generated successfully.
    content_type = response.headers.get("content-type", "")
    if "pdf" in content_type:
        disposition = response.headers.get("content-disposition", "")
        filename = "CMA_report.pdf"
        if 'filename="' in disposition:
            filename = disposition.split('filename="')[1].rstrip('"')
        size_kb = len(response.content) / 1024
        text = (
            f"CMA report generated successfully for property #{property_id}.\n"
            f"Filename: {filename}\n"
            f"Size: {size_kb:.1f} KB\n\n"
            f"The PDF is ready. To send it to a client, use the email_cma_report tool."
        )
    else:
        text = f"CMA report generated for property #{property_id}. Response: {response.text[:500]}"

    return [TextContent(type="text", text=text)]


async def handle_email_cma_report(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    recipient_email = arguments.get("recipient_email")
    recipient_name = arguments.get("recipient_name", "Client")
    agent_brand_id = arguments.get("agent_brand_id")

    if not recipient_email:
        return [TextContent(type="text", text="Error: recipient_email is required to send a CMA report.")]

    payload = {
        "property_id": property_id,
        "recipient_email": recipient_email,
        "recipient_name": recipient_name,
    }
    if agent_brand_id:
        payload["agent_brand_id"] = agent_brand_id

    response = api_post("/cma/email", json=payload)
    response.raise_for_status()
    result = response.json()

    if result.get("success"):
        text = (
            f"CMA report emailed successfully!\n"
            f"Recipient: {result.get('recipient_name', recipient_name)} <{result.get('recipient_email', recipient_email)}>\n"
            f"Property: {result.get('property_address', f'#{property_id}')}\n"
            f"Filename: {result.get('filename', 'CMA_report.pdf')}"
        )
    else:
        error = result.get("email", {}).get("error", "Unknown error")
        text = f"CMA report was generated but email failed: {error}"

    return [TextContent(type="text", text=text)]


# ── Tool Registration ──

register_tool(
    Tool(
        name="generate_cma_report",
        description=(
            "Generate a Comparative Market Analysis (CMA) PDF report for a property. "
            "Includes comparable sales, rental comps, AI-powered market analysis narrative, "
            "price recommendation, and professional agent branding. "
            "Voice examples: 'generate a CMA for the Hillsborough property', "
            "'create a comp report for property 42'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "The ID of the property (optional if address provided)",
                },
                "address": {
                    "type": "string",
                    "description": "Property address to search for (voice-friendly)",
                },
                "agent_brand_id": {
                    "type": "number",
                    "description": "Agent brand ID for custom branding (optional, defaults to property's agent brand)",
                },
            },
        },
    ),
    handle_generate_cma_report,
)

register_tool(
    Tool(
        name="email_cma_report",
        description=(
            "Generate a CMA (Comparative Market Analysis) report and email it to a client. "
            "The PDF includes comp sales, rental comps, market analysis, and agent branding. "
            "Voice examples: 'email the CMA for 123 Main St to john@example.com', "
            "'send the comp report for property 5 to the buyer'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "The ID of the property (optional if address provided)",
                },
                "address": {
                    "type": "string",
                    "description": "Property address to search for (voice-friendly)",
                },
                "recipient_email": {
                    "type": "string",
                    "description": "Email address to send the CMA report to",
                },
                "recipient_name": {
                    "type": "string",
                    "description": "Recipient's name (default: 'Client')",
                },
                "agent_brand_id": {
                    "type": "number",
                    "description": "Agent brand ID for custom branding (optional)",
                },
            },
            "required": ["recipient_email"],
        },
    ),
    handle_email_cma_report,
)
