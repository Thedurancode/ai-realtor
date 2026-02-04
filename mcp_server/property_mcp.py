#!/usr/bin/env python3
"""
Property Management MCP Server for AI Realtor
Exposes property database operations as MCP tools
"""
import asyncio
import json
import sys
from typing import Any, Optional
import requests

# Add parent directory to path for imports
sys.path.insert(0, '/Users/edduran/Documents/GitHub/ai-realtor')

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

# API Base URL
API_BASE_URL = "http://localhost:8000"


async def list_properties(limit: int = 10, status: Optional[str] = None) -> dict:
    """List properties from database"""
    params = {"limit": limit}
    if status:
        params["status"] = status

    response = requests.get(f"{API_BASE_URL}/properties/", params=params)
    response.raise_for_status()
    return response.json()


async def get_property(property_id: int) -> dict:
    """Get property details by ID"""
    response = requests.get(f"{API_BASE_URL}/properties/{property_id}")
    response.raise_for_status()
    return response.json()


async def create_property_with_address(
    address: str,
    price: float,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[float] = None,
    agent_id: int = 1,
) -> dict:
    """Create a new property with address lookup"""
    # First, autocomplete the address
    autocomplete_resp = requests.post(
        f"{API_BASE_URL}/address/autocomplete",
        json={"input": address, "country": "us"}
    )
    autocomplete_resp.raise_for_status()

    suggestions = autocomplete_resp.json()['suggestions']
    if not suggestions:
        raise ValueError(f"No address found for: {address}")

    place_id = suggestions[0]['place_id']

    # Create property
    create_resp = requests.post(
        f"{API_BASE_URL}/context/property/create",
        json={
            "place_id": place_id,
            "price": price,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "agent_id": agent_id,
            "session_id": "mcp_session"
        }
    )
    create_resp.raise_for_status()
    return create_resp.json()


async def delete_property(property_id: int) -> dict:
    """Delete a property by ID"""
    # Import here to avoid circular imports
    from app.database import SessionLocal
    from app.models.property import Property
    from app.models.zillow_enrichment import ZillowEnrichment
    from app.models.skip_trace import SkipTrace
    from app.models.contact import Contact
    from app.models.contract import Contract

    db = SessionLocal()
    try:
        property = db.query(Property).filter(Property.id == property_id).first()
        if not property:
            raise ValueError(f"Property {property_id} not found")

        address = property.address

        # Delete related data
        db.query(Contract).filter(Contract.property_id == property_id).delete()
        db.query(Contact).filter(Contact.property_id == property_id).delete()
        db.query(ZillowEnrichment).filter(ZillowEnrichment.property_id == property_id).delete()
        db.query(SkipTrace).filter(SkipTrace.property_id == property_id).delete()

        # Delete property
        db.delete(property)
        db.commit()

        return {
            "success": True,
            "message": f"Deleted property {property_id} ({address})",
            "property_id": property_id,
            "address": address
        }
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


async def enrich_property(property_id: int) -> dict:
    """Enrich property with Zillow data"""
    response = requests.post(
        f"{API_BASE_URL}/context/enrich",
        json={
            "property_ref": str(property_id),
            "session_id": "mcp_session"
        }
    )
    response.raise_for_status()
    return response.json()


async def skip_trace_property(property_id: int) -> dict:
    """Skip trace a property to find owner information"""
    response = requests.post(
        f"{API_BASE_URL}/context/skip-trace",
        json={
            "property_ref": str(property_id),
            "session_id": "mcp_session"
        }
    )
    response.raise_for_status()
    return response.json()


async def add_contact_to_property(
    property_id: int,
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    role: str = "buyer"
) -> dict:
    """Add a contact to a property"""
    response = requests.post(
        f"{API_BASE_URL}/contacts/",
        json={
            "name": name,
            "email": email,
            "phone": phone,
            "role": role,
            "property_id": property_id
        }
    )
    response.raise_for_status()
    return response.json()


# Create MCP server
app = Server("property-management")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available property management tools"""
    return [
        Tool(
            name="list_properties",
            description="List all properties in the database. Optionally filter by status (available, pending, sold). Returns property details including address, price, bedrooms, bathrooms, enrichment data, and skip trace information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of properties to return (default: 10)",
                        "default": 10
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by property status: available, pending, sold, rented, off_market",
                        "enum": ["available", "pending", "sold", "rented", "off_market"]
                    }
                }
            }
        ),
        Tool(
            name="get_property",
            description="Get detailed information for a specific property by ID. Returns complete property data including Zillow enrichment, skip trace data, photos, schools, tax history, and owner information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "The ID of the property to retrieve"
                    }
                },
                "required": ["property_id"]
            }
        ),
        Tool(
            name="create_property",
            description="Create a new property in the database. Automatically looks up full address details using Google Places API. The property will appear on the TV display.",
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Property address (will be autocompleted, e.g., '123 Main St, New York, NY')"
                    },
                    "price": {
                        "type": "number",
                        "description": "Property price in dollars"
                    },
                    "bedrooms": {
                        "type": "number",
                        "description": "Number of bedrooms"
                    },
                    "bathrooms": {
                        "type": "number",
                        "description": "Number of bathrooms"
                    },
                    "agent_id": {
                        "type": "number",
                        "description": "Agent ID (default: 1)",
                        "default": 1
                    }
                },
                "required": ["address", "price"]
            }
        ),
        Tool(
            name="delete_property",
            description="Delete a property and all its related data (enrichments, skip traces, contacts, contracts) from the database. This action cannot be undone. The property will be removed from the TV display.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "The ID of the property to delete"
                    }
                },
                "required": ["property_id"]
            }
        ),
        Tool(
            name="enrich_property",
            description="Enrich a property with comprehensive Zillow data including photos, Zestimate, rent estimate, tax history, price history, schools with ratings, property details, and market statistics. Triggers enrichment animation on TV display.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "The ID of the property to enrich"
                    }
                },
                "required": ["property_id"]
            }
        ),
        Tool(
            name="skip_trace_property",
            description="Skip trace a property to find owner contact information including name, phone numbers, email addresses, and mailing address. Useful for lead generation and outreach.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "The ID of the property to skip trace"
                    }
                },
                "required": ["property_id"]
            }
        ),
        Tool(
            name="add_contact",
            description="Add a contact (buyer, seller, agent, or other) to a property for tracking interested parties and managing relationships.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "The property ID to associate with this contact"
                    },
                    "name": {
                        "type": "string",
                        "description": "Contact's full name"
                    },
                    "email": {
                        "type": "string",
                        "description": "Contact's email address"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Contact's phone number"
                    },
                    "role": {
                        "type": "string",
                        "description": "Contact's role",
                        "enum": ["buyer", "seller", "agent", "other"],
                        "default": "buyer"
                    }
                },
                "required": ["property_id", "name"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    try:
        if name == "list_properties":
            limit = arguments.get("limit", 10)
            status = arguments.get("status")
            result = await list_properties(limit=limit, status=status)

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "get_property":
            property_id = arguments["property_id"]
            result = await get_property(property_id)

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "create_property":
            result = await create_property_with_address(
                address=arguments["address"],
                price=arguments["price"],
                bedrooms=arguments.get("bedrooms"),
                bathrooms=arguments.get("bathrooms"),
                agent_id=arguments.get("agent_id", 1)
            )

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "delete_property":
            property_id = arguments["property_id"]
            result = await delete_property(property_id)

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "enrich_property":
            property_id = arguments["property_id"]
            result = await enrich_property(property_id)

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "skip_trace_property":
            property_id = arguments["property_id"]
            result = await skip_trace_property(property_id)

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "add_contact":
            result = await add_contact_to_property(
                property_id=arguments["property_id"],
                name=arguments["name"],
                email=arguments.get("email"),
                phone=arguments.get("phone"),
                role=arguments.get("role", "buyer")
            )

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
