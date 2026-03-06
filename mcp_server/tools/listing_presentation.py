"""
Listing Presentation MCP Tools

Voice-controlled tools for generating complete listing presentations
from a property address: CMA, video script, social media posts, marketing plan, PDF, email.
"""

import json
import httpx
from typing import Any, Dict, List

from mcp.types import Tool, TextContent
from ..server import register_tool
from ..utils.http_client import API_BASE_URL


# ==========================================================================
# GENERATE LISTING PRESENTATION
# ==========================================================================

async def handle_generate_listing_presentation(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Generate a complete listing presentation from an address.

    Voice: "Create a listing presentation for 123 Main St"
    Voice: "Generate CMA and marketing plan for 456 Oak Ave"
    """
    address = arguments.get("address")
    if not address:
        return [TextContent(type="text", text="Please provide a property address.")]

    property_details = arguments.get("property_details")

    payload = {"address": address}
    if property_details:
        payload["property_details"] = property_details

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/listing-presentation/generate",
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()
        result = response.json()

    # Build a concise voice-friendly summary
    cma = result.get("cma_summary", {})
    video = result.get("video_script", {})
    posts = result.get("social_media_posts", {})
    plan = result.get("marketing_plan", [])
    talking = result.get("talking_points", [])

    lines = [
        f"Listing Presentation for {address}",
        "",
        f"Recommended List Price: {cma.get('recommended_list_price', 'N/A')}",
        f"Price Range: {cma.get('price_range_low', 'N/A')} - {cma.get('price_range_high', 'N/A')}",
        f"Avg Days on Market: {cma.get('days_on_market_avg', 'N/A')}",
        "",
        f"Marketing Plan: {len(plan)} strategies ready",
        f"Video Script: {video.get('duration', '60 seconds')} property showcase",
        f"Social Media: {len(posts)} platform posts ready",
        f"Talking Points: {len(talking)} key selling points",
        "",
        "Components generated:",
        "- CMA Summary with pricing rationale",
        "- 8-Point Marketing Plan",
        "- 4-Week Marketing Timeline",
        "- 60-Second Video Script",
        "- 5 Social Media Posts (IG, FB, X, LinkedIn, TikTok)",
        "- MLS Property Description",
        "- Just Listed Email Blast",
        "- 10 Key Selling Points",
        "",
        "Say 'email listing presentation' to send the PDF to the seller.",
    ]

    return [TextContent(type="text", text="\n".join(lines))]


# ==========================================================================
# EMAIL LISTING PRESENTATION
# ==========================================================================

async def handle_email_listing_presentation(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Generate and email a listing presentation PDF to the seller.

    Voice: "Email listing presentation for 123 Main St to john@example.com"
    Voice: "Send the listing presentation to the seller"
    """
    address = arguments.get("address")
    recipient_email = arguments.get("recipient_email")
    recipient_name = arguments.get("recipient_name", "Homeowner")
    property_details = arguments.get("property_details")

    if not address:
        return [TextContent(type="text", text="Please provide a property address.")]
    if not recipient_email:
        return [TextContent(type="text", text="Please provide a recipient email address.")]

    payload = {
        "address": address,
        "recipient_email": recipient_email,
        "recipient_name": recipient_name,
    }
    if property_details:
        payload["property_details"] = property_details

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/listing-presentation/email",
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()
        result = response.json()

    cma = result.get("presentation", {}).get("cma_summary", {})
    return [TextContent(
        type="text",
        text=(
            f"Listing presentation for {address} sent to {recipient_name} at {recipient_email}.\n"
            f"Recommended list price: {cma.get('recommended_list_price', 'N/A')}.\n"
            f"The PDF includes CMA, marketing plan, video script, social media posts, and more."
        ),
    )]


# ==========================================================================
# REGISTER TOOLS
# ==========================================================================

register_tool(
    Tool(
        name="generate_listing_presentation",
        description=(
            "Generate a complete listing presentation from a property address. "
            "Includes CMA, marketing plan, video script, social media posts, "
            "property description, email blast, talking points, and timeline. "
            "Voice: 'Create a listing presentation for 123 Main St' or "
            "'Generate CMA and marketing plan for 456 Oak Ave'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Full property address",
                },
                "property_details": {
                    "type": "object",
                    "description": "Optional property details: beds, baths, sqft, year_built, lot_size, features",
                    "properties": {
                        "beds": {"type": "number"},
                        "baths": {"type": "number"},
                        "sqft": {"type": "number"},
                        "year_built": {"type": "number"},
                        "lot_size": {"type": "string"},
                        "features": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            },
            "required": ["address"],
        },
    ),
    handle_generate_listing_presentation,
)

register_tool(
    Tool(
        name="email_listing_presentation",
        description=(
            "Generate a complete listing presentation PDF and email it to the seller. "
            "Voice: 'Email listing presentation for 123 Main St to john@example.com' or "
            "'Send the listing presentation to the seller'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Full property address",
                },
                "recipient_email": {
                    "type": "string",
                    "description": "Email address to send the presentation to",
                },
                "recipient_name": {
                    "type": "string",
                    "description": "Recipient name (default: Homeowner)",
                },
                "property_details": {
                    "type": "object",
                    "description": "Optional property details: beds, baths, sqft, year_built, lot_size, features",
                },
            },
            "required": ["address", "recipient_email"],
        },
    ),
    handle_email_listing_presentation,
)
