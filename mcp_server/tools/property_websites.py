"""
Property Website Builder MCP Tools

Voice-controlled tools for creating AI-generated landing pages for properties
Integrates with AI Realtor's property website builder
"""

import os
import httpx
from typing import Any, Dict, List
from mcp_server.types import TextContent

from app.database import SessionLocal
from app.models.property import Property
from app.models.property_website import PropertyWebsite


# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


async def handle_create_website(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Create an AI-generated landing page for a property

    Voice: "Create a landing page for property 5"
    Voice: "Generate a luxury website for the Hillsborough property"
    Voice: "Build a modern single-page site for 123 Main St"
    Voice: "Make a website for the Miami property"
    """
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    template = arguments.get("template", "modern")
    custom_name = arguments.get("custom_name")
    website_type = arguments.get("website_type", "landing_page")

    # Validate template
    valid_templates = ["modern", "luxury", "minimal", "corporate"]
    if template not in valid_templates:
        return [TextContent(
            type="text",
            text=f"Invalid template '{template}'. Valid options: {', '.join(valid_templates)}"
        )]

    db = SessionLocal()
    try:
        # Get property (by ID or address lookup)
        if property_id:
            property = db.query(Property).filter(Property.id == property_id).first()
            if not property:
                return [TextContent(
                    type="text",
                    text=f"Property {property_id} not found."
                )]
        elif address:
            # Flexible address matching
            query = address.strip().lower()
            property = db.query(Property).filter(
                Property.address.ilike(f"%{query}%")
            ).first()

            if not property:
                # Try city match
                property = db.query(Property).filter(
                    Property.city.ilike(f"%{query}%")
                ).first()

            if not property:
                return [TextContent(
                    type="text",
                    text=f"No property found matching '{address}'. Try the property ID or full address."
                )]
        else:
            return [TextContent(
                type="text",
                text="Please provide a property ID or address."
            )]

        # Get agent for API request
        agent = property.agent or db.query(Property).filter(
            Property.id == property_id
        ).first().agent

        if not agent:
            agent = db.query(Property).filter(Property.id == property.id).first().agent

        if not agent:
            # Fallback to first agent
            from app.models import Agent
            agent = db.query(Agent).first()

        # Prepare API request
        payload = {
            "website_type": website_type,
            "template": template,
            "custom_name": custom_name
        }

        # Send via API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/properties/{property.id}/websites/?agent_id={agent.id}",
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()

        # Build success message
        template_desc = {
            "modern": "Modern Design",
            "luxury": "Luxury Design",
            "minimal": "Minimalist Design",
            "corporate": "Corporate Design"
        }.get(template, template)

        return [TextContent(
            type="text",
            text=f"Created {template_desc} landing page for {property.address}, {property.city}. "
                 f"Website URL: {API_BASE_URL}{result['website_url']}. "
                 f"Preview it at: {API_BASE_URL}/properties/{property.id}/websites/{result['id']}. "
                 f"Don't forget to publish it when ready!"
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to create website: {str(e)}"
        )]
    finally:
        db.close()


async def handle_list_websites(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    List all websites for a property

    Voice: "Show me all websites for property 5"
    Voice: "What websites have been created for the Miami property?"
    Voice: "List all landing pages"
    """
    property_id = arguments.get("property_id")
    address = arguments.get("address")

    db = SessionLocal()
    try:
        # Get property (by ID or address lookup)
        if property_id:
            property = db.query(Property).filter(Property.id == property_id).first()
            if not property:
                return [TextContent(
                    type="text",
                    text=f"Property {property_id} not found."
                )]
        elif address:
            query = address.strip().lower()
            property = db.query(Property).filter(
                Property.address.ilike(f"%{query}%")
            ).first()

            if not property:
                property = db.query(Property).filter(
                    Property.city.ilike(f"%{query}%")
                ).first()

            if not property:
                return [TextContent(
                    type="text",
                    text=f"No property found matching '{address}'."
                )]
        else:
            return [TextContent(
                type="text",
                text="Please provide a property ID or address."
            )]

        # Get websites for this property
        websites = db.query(PropertyWebsite).filter(
            PropertyWebsite.property_id == property.id
        ).order_by(PropertyWebsite.created_at.desc()).all()

        if not websites:
            return [TextContent(
                type="text",
                text=f"No websites found for {property.address}, {property.city}. "
                     f"Create one with: 'Create a landing page for property {property.id}'"
            )]

        # Build summary
        summary_lines = [f"Websites for {property.address}, {property.city}:"]
        for w in websites:
            status = "Published" if w.is_published else "Draft"
            views = sum(1 for a in w.analytics if a.event_type == "view") if w.analytics else 0
            summary_lines.append(
                f"  • {w.website_name} ({w.template}) - {status} "
                f"({views} views) - Created {w.created_at.strftime('%b %d')}"
            )

        return [TextContent(
            type="text",
            text="\n".join(summary_lines)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to list websites: {str(e)}"
        )]
    finally:
        db.close()


async def handle_publish_website(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Publish a website (make it publicly accessible)

    Voice: "Publish the landing page for property 5"
    Voice: "Go live with website 3"
    Voice: "Publish the luxury website for 123 Main St"
    """
    website_id = arguments.get("website_id")
    property_id = arguments.get("property_id")

    if not website_id:
        return [TextContent(
            type="text",
            text="Please provide a website ID to publish."
        )]

    try:
        async with httpx.AsyncClient() as client:
            url = f"{API_BASE_URL}/properties/{property_id or 1}/websites/{website_id}/publish"
            response = await client.post(url, timeout=30.0)
            response.raise_for_status()
            result = response.json()

        return [TextContent(
            type="text",
            text=f"Website published successfully! "
                 f"Public URL: {API_BASE_URL}{result['website_url']}"
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to publish website: {str(e)}"
        )]


async def handle_unpublish_website(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Unpublish a website (make it private)

    Voice: "Unpublish the landing page for property 5"
    Voice: "Take website 3 offline"
    Voice: "Make the luxury website private"
    """
    website_id = arguments.get("website_id")
    property_id = arguments.get("property_id")

    if not website_id:
        return [TextContent(
            type="text",
            text="Please provide a website ID to unpublish."
        )]

    try:
        async with httpx.AsyncClient() as client:
            url = f"{API_BASE_URL}/properties/{property_id or 1}/websites/{website_id}/unpublish"
            response = await client.post(url, timeout=30.0)
            response.raise_for_status()

        return [TextContent(
            type="text",
            text=f"Website {website_id} has been unpublished and is now private."
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to unpublish website: {str(e)}"
        )]


async def handle_get_analytics(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Get analytics for a website

    Voice: "Show analytics for the landing page on property 5"
    Voice: "How is website 3 performing?"
    Voice: "Get stats for the luxury website"
    """
    website_id = arguments.get("website_id")
    property_id = arguments.get("property_id")
    days = arguments.get("days", 30)

    if not website_id:
        return [TextContent(
            type="text",
            text="Please provide a website ID."
        )]

    try:
        async with httpx.AsyncClient() as client:
            url = f"{API_BASE_URL}/properties/{property_id or 1}/websites/{website_id}/analytics?days={days}"
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            result = response.json()

        # Build summary
        summary_lines = [
            f"Analytics for {result.get('website_name', f'Website {website_id}')}:",
            f"  Period: Last {days} days",
            f"  Total Events: {result['total_events']}"
        ]

        if result['events_by_type']:
            summary_lines.append("  Breakdown:")
            for event_type, count in result['events_by_type'].items():
                summary_lines.append(f"    • {event_type.replace('_', ' ').title()}: {count}")

        return [TextContent(
            type="text",
            text="\n".join(summary_lines)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to get analytics: {str(e)}"
        )]


async def handle_delete_website(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Delete a website permanently

    Voice: "Delete website 3"
    Voice: "Remove the landing page for property 5"
    """
    website_id = arguments.get("website_id")
    property_id = arguments.get("property_id")

    if not website_id:
        return [TextContent(
            type="text",
            text="Please provide a website ID to delete."
        )]

    try:
        async with httpx.AsyncClient() as client:
            url = f"{API_BASE_URL}/properties/{property_id or 1}/websites/{website_id}"
            response = await client.delete(url, timeout=30.0)
            response.raise_for_status()
            result = response.json()

        return [TextContent(
            type="text",
            text=result.get('message', f'Website {website_id} deleted successfully.')
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to delete website: {str(e)}"
        )]


async def handle_update_website(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Update website content or settings

    Voice: "Update website 3 name to Luxury Home"
    Voice: "Change the template of website 5 to luxury"
    """
    website_id = arguments.get("website_id")
    property_id = arguments.get("property_id")
    website_name = arguments.get("website_name")
    template = arguments.get("template")

    if not website_id:
        return [TextContent(
            type="text",
            text="Please provide a website ID."
        )]

    if not any([website_name, template]):
        return [TextContent(
            type="text",
            text="Please provide something to update (website_name or template)."
        )]

    try:
        payload = {}
        if website_name:
            payload["website_name"] = website_name
        if template:
            payload["template"] = template

        async with httpx.AsyncClient() as client:
            url = f"{API_BASE_URL}/properties/{property_id or 1}/websites/{website_id}"
            response = await client.put(url, json=payload, timeout=30.0)
            response.raise_for_status()
            result = response.json()

        updates = ", ".join(payload.keys())
        return [TextContent(
            type="text",
            text=f"Website updated: {updates}. "
                 f"Updated at: {result.get('updated_at', 'Just now')}"
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to update website: {str(e)}"
        )]


# Register all tools
from mcp.types import Tool
from ..server import register_tool

__all__ = [
    "handle_create_website",
    "handle_list_websites",
    "handle_publish_website",
    "handle_unpublish_website",
    "handle_get_analytics",
    "handle_delete_website",
    "handle_update_website"
]

# Tool registrations with schemas
register_tool(
    Tool(
        name="create_property_website",
        description="Create an AI-generated landing page for a property. Voice: 'Create a landing page for property 5' or 'Build a luxury website for the Miami property'. Templates: modern, luxury, minimal, corporate.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "number", "description": "Property ID"},
                "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main St' or 'the Miami property')"},
                "template": {"type": "string", "description": "Website template", "enum": ["modern", "luxury", "minimal", "corporate"], "default": "modern"},
                "custom_name": {"type": "string", "description": "Custom name for the website"},
                "website_type": {"type": "string", "description": "Type of website", "enum": ["landing_page", "single_page", "multi_page"], "default": "landing_page"}
            }
        }
    ),
    handle_create_website
)

register_tool(
    Tool(
        name="list_property_websites",
        description="List all websites for a property. Voice: 'Show me all websites for property 5' or 'What websites exist for the Miami property?'.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "number", "description": "Property ID"},
                "address": {"type": "string", "description": "Property address to search for"}
            }
        }
    ),
    handle_list_websites
)

register_tool(
    Tool(
        name="publish_property_website",
        description="Publish a website to make it publicly accessible. Voice: 'Publish the landing page for property 5' or 'Go live with website 3'.",
        inputSchema={
            "type": "object",
            "properties": {
                "website_id": {"type": "number", "description": "Website ID to publish"},
                "property_id": {"type": "number", "description": "Property ID"}
            },
            "required": ["website_id"]
        }
    ),
    handle_publish_website
)

register_tool(
    Tool(
        name="unpublish_property_website",
        description="Unpublish a website to make it private. Voice: 'Unpublish the landing page for property 5' or 'Take website 3 offline'.",
        inputSchema={
            "type": "object",
            "properties": {
                "website_id": {"type": "number", "description": "Website ID to unpublish"},
                "property_id": {"type": "number", "description": "Property ID"}
            },
            "required": ["website_id"]
        }
    ),
    handle_unpublish_website
)

register_tool(
    Tool(
        name="get_website_analytics",
        description="Get analytics for a website (views, form submissions, inquiries). Voice: 'Show analytics for the landing page on property 5' or 'How is website 3 performing?'.",
        inputSchema={
            "type": "object",
            "properties": {
                "website_id": {"type": "number", "description": "Website ID"},
                "property_id": {"type": "number", "description": "Property ID"},
                "days": {"type": "number", "description": "Number of days to look back", "default": 30}
            },
            "required": ["website_id"]
        }
    ),
    handle_get_analytics
)

register_tool(
    Tool(
        name="delete_property_website",
        description="Delete a website permanently. Voice: 'Delete website 3' or 'Remove the landing page for property 5'.",
        inputSchema={
            "type": "object",
            "properties": {
                "website_id": {"type": "number", "description": "Website ID to delete"},
                "property_id": {"type": "number", "description": "Property ID"}
            },
            "required": ["website_id"]
        }
    ),
    handle_delete_website
)

register_tool(
    Tool(
        name="update_property_website",
        description="Update website content or settings. Voice: 'Update website 3 name to Luxury Home' or 'Change the template of website 5 to luxury'.",
        inputSchema={
            "type": "object",
            "properties": {
                "website_id": {"type": "number", "description": "Website ID to update"},
                "property_id": {"type": "number", "description": "Property ID"},
                "website_name": {"type": "string", "description": "New website name"},
                "template": {"type": "string", "description": "New template", "enum": ["modern", "luxury", "minimal", "corporate"]}
            },
            "required": ["website_id"]
        }
    ),
    handle_update_website
)
