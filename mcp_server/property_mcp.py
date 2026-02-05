#!/usr/bin/env python3
"""
Property Management MCP Server for AI Realtor
Exposes property database operations as MCP tools
"""
import asyncio
import json
import sys
import time
from typing import Any, Optional
import requests

# Add parent directory to path for imports
sys.path.insert(0, '/Users/edduran/Documents/GitHub/ai-realtor')

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

# API Base URL
API_BASE_URL = "http://localhost:8000"

# Helper function to log activity events
def log_activity_event(tool_name: str, metadata: dict = None) -> Optional[int]:
    """Log an activity event for MCP tool call"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/activities/log",
            json={
                "tool_name": tool_name,
                "user_source": "Claude Desktop MCP",
                "event_type": "tool_call",
                "status": "pending",
                "metadata": metadata
            },
            timeout=1  # Don't block tool execution
        )
        if response.status_code == 200:
            return response.json().get("id")
    except Exception as e:
        print(f"Warning: Failed to log activity: {e}")
    return None

def update_activity_event(event_id: int, status: str, duration_ms: int, error_message: str = None):
    """Update activity event with result"""
    if not event_id:
        return
    try:
        requests.patch(
            f"{API_BASE_URL}/activities/{event_id}",
            json={
                "status": status,
                "duration_ms": duration_ms,
                "error_message": error_message
            },
            timeout=1
        )
    except Exception as e:
        print(f"Warning: Failed to update activity: {e}")


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


async def send_notification(
    title: str,
    message: str,
    notification_type: str = "general",
    priority: str = "medium",
    icon: str = "🔔",
    property_id: Optional[int] = None,
    auto_dismiss_seconds: int = 10
) -> dict:
    """Send a custom notification to the TV display"""
    response = requests.post(
        f"{API_BASE_URL}/notifications/",
        json={
            "type": notification_type,
            "priority": priority,
            "title": title,
            "message": message,
            "icon": icon,
            "property_id": property_id,
            "auto_dismiss_seconds": auto_dismiss_seconds
        }
    )
    response.raise_for_status()
    return response.json()


async def list_notifications(limit: int = 10, unread_only: bool = False) -> dict:
    """List recent notifications"""
    params = {"limit": limit}
    if unread_only:
        params["unread_only"] = "true"

    response = requests.get(f"{API_BASE_URL}/notifications/", params=params)
    response.raise_for_status()
    return response.json()


async def send_contract(
    property_id: int,
    contact_id: int,
    contract_name: str = "Purchase Agreement",
    docuseal_template_id: Optional[str] = None
) -> dict:
    """Send a contract to a contact for signing"""
    # Create contract if needed
    response = requests.post(
        f"{API_BASE_URL}/contracts/",
        json={
            "property_id": property_id,
            "contact_id": contact_id,
            "name": contract_name,
            "docuseal_template_id": docuseal_template_id or "1"
        }
    )
    response.raise_for_status()
    contract = response.json()

    # Send to contact
    response = requests.post(
        f"{API_BASE_URL}/contracts/{contract['id']}/send-to-contact",
        json={"contact_id": contact_id}
    )
    response.raise_for_status()
    return response.json()


async def check_contract_status(contract_id: Optional[int] = None, address_query: Optional[str] = None) -> dict:
    """Check the status of a contract by ID or property address"""
    if address_query:
        # Find property by address, then get contracts for that property
        contracts = await list_contracts(address_query=address_query)
        if not contracts or len(contracts) == 0:
            raise ValueError(f"No contracts found for address: {address_query}")
        # Return the most recent contract
        return await check_contract_status(contract_id=contracts[0]['id'])

    if not contract_id:
        raise ValueError("Either contract_id or address_query must be provided")

    response = requests.get(
        f"{API_BASE_URL}/contracts/{contract_id}/status",
        params={"refresh": "true"}
    )
    response.raise_for_status()
    return response.json()


def normalize_voice_query(query: str) -> list[str]:
    """Normalize voice input for better matching - returns list of variations"""
    import re

    # 1. Remove filler words
    fillers = ['um', 'uh', 'like', 'you know', 'so', 'well', 'the contract for',
               'contracts for', 'the property at', 'show me', 'check', 'list',
               'get', 'find', 'please', 'can you', 'could you', 'would you']
    query_clean = query.lower()
    for filler in fillers:
        query_clean = query_clean.replace(filler, ' ')
    query_clean = ' '.join(query_clean.split())

    # 2. Convert written numbers to digits
    number_words = {
        'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
        'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
        'eleven': '11', 'twelve': '12', 'twenty': '20', 'thirty': '30',
        'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
        'eighty': '80', 'ninety': '90', 'hundred': '100'
    }
    for word, digit in number_words.items():
        query_clean = re.sub(r'\b' + word + r'\b', digit, query_clean)

    # Handle "one forty one" → "141"
    query_clean = re.sub(r'\b(\d+)\s+(\d+)\s+(\d+)\b', r'\1\2\3', query_clean)
    query_clean = re.sub(r'\b(\d+)\s+(\d+)\b', r'\1\2', query_clean)

    # 3. Expand abbreviations
    abbreviations = {
        r'\bst\b': 'street', r'\bave\b': 'avenue', r'\bblvd\b': 'boulevard',
        r'\bdr\b': 'drive', r'\brd\b': 'road', r'\bln\b': 'lane',
        r'\bct\b': 'court', r'\bpl\b': 'place', r'\bapt\b': 'apartment',
    }
    for abbr, full in abbreviations.items():
        query_clean = re.sub(abbr, full, query_clean)

    # 4. Generate phonetic variations
    variations = [query_clean]
    phonetic_map = {
        'throop': ['troop', 'throup', 'trupe', 'troup'],
        'street': ['strait', 'streat'],
        'avenue': ['avenu', 'av'],
    }

    for correct, alternates in phonetic_map.items():
        if correct in query_clean:
            for alt in alternates:
                variations.append(query_clean.replace(correct, alt))
        for alt in alternates:
            if alt in query_clean:
                variations.append(query_clean.replace(alt, correct))

    return variations


async def list_contracts(property_id: Optional[int] = None, address_query: Optional[str] = None) -> dict:
    """List contracts, optionally filtered by property ID or address (voice-optimized)"""
    # If address provided, find property first
    if address_query:
        # Use context endpoint to find property by address
        from app.database import SessionLocal
        from app.models.property import Property
        from sqlalchemy import func, or_

        db = SessionLocal()
        try:
            # Voice-optimized: normalize query and generate variations
            query_variations = normalize_voice_query(address_query)

            # Search using all variations
            properties = db.query(Property).filter(
                or_(*[func.lower(Property.address).contains(var) for var in query_variations])
            ).all()

            if not properties:
                # Fuzzy match fallback
                from difflib import get_close_matches
                all_addresses = [p.address.lower() for p in db.query(Property).limit(100).all()]
                matches = get_close_matches(query_variations[0], all_addresses, n=3, cutoff=0.6)

                if matches:
                    raise ValueError(
                        f"No exact match for '{address_query}'.\n" +
                        f"Did you mean: {', '.join(matches)}?"
                    )
                raise ValueError(f"No property found matching address: {address_query}")

            # Use the first matching property (most relevant)
            property_id = properties[0].id
        finally:
            db.close()

    if property_id:
        url = f"{API_BASE_URL}/contracts/property/{property_id}"
    else:
        url = f"{API_BASE_URL}/contracts/"

    response = requests.get(url)
    response.raise_for_status()
    return response.json()


async def list_contracts_voice(address_query: str) -> dict:
    """
    Voice-optimized contract listing with enhanced response formatting.
    Designed specifically for voice assistants (Siri, Alexa, Google Assistant).
    """
    # Use the enhanced list_contracts with voice normalization
    contracts = await list_contracts(address_query=address_query)

    if not contracts or len(contracts) == 0:
        return {
            "voice_response": f"No contracts found for {address_query}.",
            "contracts": [],
            "count": 0
        }

    # Get property address for response
    from app.database import SessionLocal
    from app.models.property import Property

    db = SessionLocal()
    try:
        query_variations = normalize_voice_query(address_query)
        from sqlalchemy import func, or_

        property_obj = db.query(Property).filter(
            or_(*[func.lower(Property.address).contains(var) for var in query_variations])
        ).first()

        property_address = property_obj.address if property_obj else address_query
    finally:
        db.close()

    # Format for voice response
    count = len(contracts)

    if count == 1:
        contract = contracts[0]
        status = contract['status'].replace('_', ' ')
        voice_response = (
            f"Found one contract for {property_address}. "
            f"It's a {contract['name']} with status {status}."
        )
    else:
        # Count by status
        status_counts = {}
        for c in contracts:
            status = c['status']
            status_counts[status] = status_counts.get(status, 0) + 1

        status_summary = ', '.join([
            f"{count} {status.replace('_', ' ')}"
            for status, count in status_counts.items()
        ])

        voice_response = (
            f"Found {count} contracts for {property_address}. "
            f"Status breakdown: {status_summary}."
        )

    return {
        "voice_response": voice_response,
        "contracts": contracts,
        "count": count,
        "address": property_address
    }


async def check_contract_status_voice(address_query: str) -> dict:
    """
    Voice-optimized contract status check with natural language response.
    Returns contract status in a format optimized for voice output.
    """
    # Use existing check with voice normalization
    result = await check_contract_status(address_query=address_query)

    # Extract key info
    contract_id = result.get('id', 'unknown')
    status = result.get('status', 'unknown').replace('_', ' ')
    contract_name = result.get('name', 'contract')

    # Build voice response
    voice_response = f"Contract number {contract_id}, the {contract_name}, is {status}. "

    # Add signer information
    if 'submitters' in result and result['submitters']:
        submitters = result['submitters']
        total = len(submitters)
        completed = sum(1 for s in submitters if s.get('status') == 'completed')

        voice_response += f"{completed} of {total} signers have completed. "

        # List pending signers
        pending = [s['name'] for s in submitters if s.get('status') != 'completed']
        if pending:
            if len(pending) == 1:
                voice_response += f"Still waiting on {pending[0]}."
            else:
                voice_response += f"Still waiting on: {', '.join(pending[:-1])}, and {pending[-1]}."
        else:
            voice_response += "All signers have completed!"

    return {
        "voice_response": voice_response,
        "contract_id": contract_id,
        "status": status,
        "full_details": result
    }


async def check_property_contract_readiness(property_id: Optional[int] = None, address_query: Optional[str] = None) -> dict:
    """
    Check if property has all required contracts signed and is ready to close.
    Returns readiness status with breakdown of completed/in-progress/missing contracts.
    """
    # Find property if address provided
    if address_query and not property_id:
        from app.database import SessionLocal
        from app.models.property import Property
        from sqlalchemy import func, or_

        db = SessionLocal()
        try:
            query_variations = normalize_voice_query(address_query)
            property_obj = db.query(Property).filter(
                or_(*[func.lower(Property.address).contains(var) for var in query_variations])
            ).first()

            if not property_obj:
                raise ValueError(f"No property found matching: {address_query}")

            property_id = property_obj.id
        finally:
            db.close()

    if not property_id:
        raise ValueError("Either property_id or address_query must be provided")

    response = requests.get(f"{API_BASE_URL}/contracts/property/{property_id}/required-status")
    response.raise_for_status()
    return response.json()


async def check_property_contract_readiness_voice(address_query: str) -> dict:
    """
    Voice-optimized check if property is ready to close.
    Returns natural language response about contract completion status.
    """
    result = await check_property_contract_readiness(address_query=address_query)

    property_address = result.get('property_address', address_query)
    is_ready = result.get('is_ready_to_close', False)
    total = result.get('total_required', 0)
    completed = result.get('completed', 0)
    in_progress = result.get('in_progress', 0)
    missing = result.get('missing', 0)

    if is_ready:
        voice_response = (
            f"Great news! {property_address} is ready to close. "
            f"All {total} required contracts have been completed and signed."
        )
    else:
        voice_response = f"{property_address} is not ready to close yet. "

        status_parts = []
        if completed > 0:
            status_parts.append(f"{completed} contract{'s' if completed != 1 else ''} completed")
        if in_progress > 0:
            status_parts.append(f"{in_progress} in progress")
        if missing > 0:
            status_parts.append(f"{missing} missing")

        if status_parts:
            voice_response += "Status: " + ", ".join(status_parts) + ". "

        # Add missing contract details
        if missing > 0 and result.get('missing_templates'):
            voice_response += "Missing contracts: "
            missing_names = [t['name'] for t in result['missing_templates'][:3]]
            voice_response += ", ".join(missing_names)
            if len(result['missing_templates']) > 3:
                voice_response += f", and {len(result['missing_templates']) - 3} more"
            voice_response += "."

    return {
        "voice_response": voice_response,
        "is_ready_to_close": is_ready,
        "total_required": total,
        "completed": completed,
        "in_progress": in_progress,
        "missing": missing,
        "property_address": property_address,
        "full_details": result
    }


async def attach_required_contracts(property_id: Optional[int] = None, address_query: Optional[str] = None) -> dict:
    """
    Manually trigger auto-attach of required contracts to a property.
    Useful if property was created before templates were configured.
    """
    # Find property if address provided
    if address_query and not property_id:
        from app.database import SessionLocal
        from app.models.property import Property
        from sqlalchemy import func, or_

        db = SessionLocal()
        try:
            query_variations = normalize_voice_query(address_query)
            property_obj = db.query(Property).filter(
                or_(*[func.lower(Property.address).contains(var) for var in query_variations])
            ).first()

            if not property_obj:
                raise ValueError(f"No property found matching: {address_query}")

            property_id = property_obj.id
        finally:
            db.close()

    if not property_id:
        raise ValueError("Either property_id or address_query must be provided")

    response = requests.post(f"{API_BASE_URL}/contracts/property/{property_id}/auto-attach")
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
        ),
        Tool(
            name="send_notification",
            description="Send a custom notification to the TV display. Use this to alert about important events, milestones, or custom messages. The notification will appear as an animated toast on the TV display.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Notification title (concise, under 50 chars)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Notification message"
                    },
                    "notification_type": {
                        "type": "string",
                        "description": "Type of notification",
                        "enum": ["general", "contract_signed", "new_lead", "property_price_change", "property_status_change", "appointment_reminder", "skip_trace_complete", "enrichment_complete"],
                        "default": "general"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority level (affects color)",
                        "enum": ["low", "medium", "high", "urgent"],
                        "default": "medium"
                    },
                    "icon": {
                        "type": "string",
                        "description": "Emoji icon to display (e.g., 🎉, ⚠️, 📝)",
                        "default": "🔔"
                    },
                    "property_id": {
                        "type": "number",
                        "description": "Optional property ID to associate"
                    },
                    "auto_dismiss_seconds": {
                        "type": "number",
                        "description": "Auto-dismiss after X seconds (5-30, default: 10)",
                        "default": 10
                    }
                },
                "required": ["title", "message"]
            }
        ),
        Tool(
            name="list_notifications",
            description="List recent notifications from the system. Shows notification history including contracts signed, new leads, price changes, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Number of notifications to return (default: 10)",
                        "default": 10
                    },
                    "unread_only": {
                        "type": "boolean",
                        "description": "Only show unread notifications",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="send_contract",
            description="Send a contract to a contact for signing via DocuSeal. The contact will receive an email with a signing link. This automatically creates the contract if it doesn't exist and sends it for e-signature.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "The property ID this contract is for"
                    },
                    "contact_id": {
                        "type": "number",
                        "description": "The contact ID who should sign (must be associated with the property)"
                    },
                    "contract_name": {
                        "type": "string",
                        "description": "Name of the contract (e.g., 'Purchase Agreement', 'Lease Agreement')",
                        "default": "Purchase Agreement"
                    },
                    "docuseal_template_id": {
                        "type": "string",
                        "description": "DocuSeal template ID (optional, defaults to '1')"
                    }
                },
                "required": ["property_id", "contact_id"]
            }
        ),
        Tool(
            name="check_contract_status",
            description="Check the current status of a contract by ID or property address. VOICE-OPTIMIZED: Handles phonetic variations ('troop' → 'throop'), number transcriptions ('one forty one' → '141'), filler words, and conversational input. Returns detailed information including signing status, submitters, and timestamps. Refreshes status from DocuSeal API.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_id": {
                        "type": "number",
                        "description": "The contract ID to check (optional if address_query provided)"
                    },
                    "address_query": {
                        "type": "string",
                        "description": "Natural language address (voice-friendly). Examples: 'one forty one throop', 'troop avenue', '23 main st'. Handles phonetic variations and number conversions automatically."
                    }
                }
            }
        ),
        Tool(
            name="list_contracts",
            description="List contracts, optionally filtered by property ID or address. VOICE-OPTIMIZED: Handles phonetic variations, number transcriptions ('twenty three' → '23'), filler words ('um show me contracts for...'), and conversational queries. Shows contract details including name, status, property, and signing progress.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "Optional: filter contracts for a specific property ID"
                    },
                    "address_query": {
                        "type": "string",
                        "description": "Optional: natural language address (voice-friendly). Examples: 'contracts for troop ave', 'um one forty one throop', 'twenty three main street'. Handles phonetic and conversational input automatically."
                    }
                }
            }
        ),
        Tool(
            name="list_contracts_voice",
            description="🎤 VOICE ASSISTANT TOOL: List contracts with voice-optimized response. Specifically designed for voice assistants (Siri, Alexa, Google Assistant). Returns contracts with natural language response suitable for text-to-speech. Handles all voice input challenges (phonetic errors, number transcriptions, filler words).",
            inputSchema={
                "type": "object",
                "properties": {
                    "address_query": {
                        "type": "string",
                        "description": "Natural language address from voice input. Examples: 'one forty one troop', 'um show contracts for main street', 'twenty three oak avenue'. All voice variations handled automatically."
                    }
                },
                "required": ["address_query"]
            }
        ),
        Tool(
            name="check_contract_status_voice",
            description="🎤 VOICE ASSISTANT TOOL: Check contract status with voice-optimized response. Specifically designed for voice assistants (Siri, Alexa, Google Assistant). Returns status in natural language format suitable for text-to-speech. Example response: 'Contract 23 is in progress. 1 of 2 signers have completed. Still waiting on Michael Chen.'",
            inputSchema={
                "type": "object",
                "properties": {
                    "address_query": {
                        "type": "string",
                        "description": "Natural language address from voice input. Examples: 'check status for one forty one throop', 'troop avenue', 'main street'. Handles phonetic variations and number conversions."
                    }
                },
                "required": ["address_query"]
            }
        ),
        Tool(
            name="check_property_contract_readiness",
            description="Check if a property has all required contracts completed and is ready to close. Returns breakdown of completed/in-progress/missing contracts. Works with property ID or address query (voice-optimized).",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "Property ID to check (optional if address_query provided)"
                    },
                    "address_query": {
                        "type": "string",
                        "description": "Natural language address (voice-friendly). Examples: 'one forty one throop', 'main street'. Handles phonetic variations."
                    }
                }
            }
        ),
        Tool(
            name="check_property_contract_readiness_voice",
            description="🎤 VOICE ASSISTANT TOOL: Check if property is ready to close with voice-optimized response. Returns natural language summary of contract completion status. Example: 'Great news! 141 Throop is ready to close. All 3 required contracts have been completed.' Perfect for asking 'Is this property ready to close?'",
            inputSchema={
                "type": "object",
                "properties": {
                    "address_query": {
                        "type": "string",
                        "description": "Natural language address from voice input. Examples: 'is one forty one throop ready to close', 'check if main street is ready'. Handles phonetic variations."
                    }
                },
                "required": ["address_query"]
            }
        ),
        Tool(
            name="attach_required_contracts",
            description="Manually attach required contracts to a property. The system will identify applicable contract templates based on property state, type, and price, then auto-attach them. Useful for existing properties that were created before contract templates were configured.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "Property ID (optional if address_query provided)"
                    },
                    "address_query": {
                        "type": "string",
                        "description": "Natural language address (voice-friendly). Examples: 'attach contracts to one forty one throop', 'main street'. Handles phonetic variations."
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    # Log activity start
    start_time = time.time()
    event_id = log_activity_event(tool_name=name, metadata=arguments)

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

        elif name == "send_notification":
            result = await send_notification(
                title=arguments["title"],
                message=arguments["message"],
                notification_type=arguments.get("notification_type", "general"),
                priority=arguments.get("priority", "medium"),
                icon=arguments.get("icon", "🔔"),
                property_id=arguments.get("property_id"),
                auto_dismiss_seconds=arguments.get("auto_dismiss_seconds", 10)
            )

            return [TextContent(
                type="text",
                text=f"✅ Notification sent to TV display!\n\n{json.dumps(result, indent=2)}"
            )]

        elif name == "list_notifications":
            limit = arguments.get("limit", 10)
            unread_only = arguments.get("unread_only", False)
            result = await list_notifications(limit=limit, unread_only=unread_only)

            if isinstance(result, list) and len(result) > 0:
                summary = f"Found {len(result)} notification(s):\n\n"
                for notif in result:
                    summary += f"{notif.get('icon', '🔔')} {notif['title']}\n"
                    summary += f"   {notif['message']}\n"
                    summary += f"   Type: {notif['type']} | Priority: {notif['priority']}\n"
                    summary += f"   Created: {notif['created_at']}\n\n"

                return [TextContent(
                    type="text",
                    text=summary + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text="No notifications found."
                )]

        elif name == "send_contract":
            result = await send_contract(
                property_id=arguments["property_id"],
                contact_id=arguments["contact_id"],
                contract_name=arguments.get("contract_name", "Purchase Agreement"),
                docuseal_template_id=arguments.get("docuseal_template_id")
            )

            return [TextContent(
                type="text",
                text=f"✅ Contract sent for signing!\n\n{json.dumps(result, indent=2)}"
            )]

        elif name == "check_contract_status":
            contract_id = arguments.get("contract_id")
            address_query = arguments.get("address_query")
            result = await check_contract_status(contract_id=contract_id, address_query=address_query)

            # Format status
            contract_id_display = result.get('id', contract_id or 'unknown')
            status_text = f"Contract #{contract_id_display} Status: {result.get('status', 'unknown').upper()}\n\n"

            if "submitters" in result and result["submitters"]:
                status_text += "Signers:\n"
                for submitter in result["submitters"]:
                    name = submitter.get("name", "Unknown")
                    role = submitter.get("role", "Unknown")
                    status = submitter.get("status", "pending")
                    status_text += f"  - {name} ({role}): {status}\n"

            return [TextContent(
                type="text",
                text=status_text + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
            )]

        elif name == "list_contracts":
            property_id = arguments.get("property_id")
            address_query = arguments.get("address_query")
            result = await list_contracts(property_id=property_id, address_query=address_query)

            if isinstance(result, list) and len(result) > 0:
                summary = f"Found {len(result)} contract(s)"
                if address_query:
                    summary += f" for address '{address_query}'"
                summary += ":\n\n"

                for contract in result:
                    summary += f"📝 {contract['name']} (ID: {contract['id']})\n"
                    summary += f"   Status: {contract.get('status', 'unknown')}\n"
                    if contract.get('property_id'):
                        summary += f"   Property ID: {contract['property_id']}\n"
                    summary += f"   Created: {contract.get('created_at', 'N/A')}\n\n"

                return [TextContent(
                    type="text",
                    text=summary + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"No contracts found{' for address: ' + address_query if address_query else ''}."
                )]

        elif name == "list_contracts_voice":
            address_query = arguments["address_query"]
            result = await list_contracts_voice(address_query=address_query)

            # Format for voice output
            voice_text = f"🎤 VOICE RESPONSE:\n{result['voice_response']}\n\n"
            voice_text += f"📊 DETAILS:\n"
            voice_text += f"Count: {result['count']}\n"
            voice_text += f"Address: {result.get('address', address_query)}\n\n"

            if result['contracts']:
                voice_text += "📝 CONTRACTS:\n"
                for contract in result['contracts']:
                    voice_text += f"  • {contract['name']} ({contract['status']})\n"

            return [TextContent(
                type="text",
                text=voice_text + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
            )]

        elif name == "check_contract_status_voice":
            address_query = arguments["address_query"]
            result = await check_contract_status_voice(address_query=address_query)

            # Format for voice output
            voice_text = f"🎤 VOICE RESPONSE:\n{result['voice_response']}\n\n"
            voice_text += f"📊 DETAILS:\n"
            voice_text += f"Contract ID: {result['contract_id']}\n"
            voice_text += f"Status: {result['status']}\n"

            return [TextContent(
                type="text",
                text=voice_text + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
            )]

        elif name == "check_property_contract_readiness":
            property_id = arguments.get("property_id")
            address_query = arguments.get("address_query")
            result = await check_property_contract_readiness(property_id=property_id, address_query=address_query)

            # Format readiness report
            is_ready = result.get('is_ready_to_close', False)
            ready_emoji = "✅" if is_ready else "⚠️"

            report = f"{ready_emoji} CONTRACT READINESS REPORT\n\n"
            report += f"Property: {result.get('property_address', 'Unknown')}\n"
            report += f"Ready to Close: {'YES' if is_ready else 'NO'}\n\n"
            report += f"📊 STATUS:\n"
            report += f"  Total Required: {result.get('total_required', 0)}\n"
            report += f"  ✅ Completed: {result.get('completed', 0)}\n"
            report += f"  ⏳ In Progress: {result.get('in_progress', 0)}\n"
            report += f"  ❌ Missing: {result.get('missing', 0)}\n"

            if result.get('missing_templates'):
                report += f"\n❌ MISSING CONTRACTS:\n"
                for template in result['missing_templates']:
                    report += f"  • {template['name']}\n"

            if result.get('incomplete_contracts'):
                report += f"\n⏳ IN PROGRESS:\n"
                for contract in result['incomplete_contracts']:
                    report += f"  • {contract['name']} ({contract['status']})\n"

            return [TextContent(
                type="text",
                text=report + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
            )]

        elif name == "check_property_contract_readiness_voice":
            address_query = arguments["address_query"]
            result = await check_property_contract_readiness_voice(address_query=address_query)

            # Format for voice output
            is_ready_emoji = "✅" if result['is_ready_to_close'] else "⚠️"
            voice_text = f"{is_ready_emoji} 🎤 VOICE RESPONSE:\n{result['voice_response']}\n\n"
            voice_text += f"📊 SUMMARY:\n"
            voice_text += f"  Property: {result.get('property_address', 'Unknown')}\n"
            voice_text += f"  Ready to Close: {'YES' if result['is_ready_to_close'] else 'NO'}\n"
            voice_text += f"  Required Contracts: {result['total_required']}\n"
            voice_text += f"  Completed: {result['completed']}\n"
            voice_text += f"  In Progress: {result['in_progress']}\n"
            voice_text += f"  Missing: {result['missing']}\n"

            return [TextContent(
                type="text",
                text=voice_text + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
            )]

        elif name == "attach_required_contracts":
            property_id = arguments.get("property_id")
            address_query = arguments.get("address_query")
            result = await attach_required_contracts(property_id=property_id, address_query=address_query)

            # Format result
            attached_count = result.get('contracts_attached', 0)
            contracts_text = f"✅ CONTRACTS AUTO-ATTACHED\n\n"
            contracts_text += f"Property: {result.get('property_address', 'Unknown')}\n"
            contracts_text += f"Contracts Attached: {attached_count}\n\n"

            if attached_count > 0:
                contracts_text += f"📝 ATTACHED CONTRACTS:\n"
                for contract in result.get('contracts', []):
                    contracts_text += f"  • {contract['name']} ({contract['status']})\n"
            else:
                contracts_text += "ℹ️ No new contracts attached (all applicable contracts already exist)\n"

            return [TextContent(
                type="text",
                text=contracts_text + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
            )]

        else:
            raise ValueError(f"Unknown tool: {name}")

        # Log success - this is reached for all successful tool calls
        # However, we need to intercept the return to log before returning
        # This is a limitation - we'll add logging in the except for errors

    except Exception as e:
        # Log error
        duration_ms = int((time.time() - start_time) * 1000)
        update_activity_event(event_id, status="error", duration_ms=duration_ms, error_message=str(e))

        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    finally:
        # Log success if no exception was raised
        duration_ms = int((time.time() - start_time) * 1000)
        # We'll check if event exists and hasn't been updated (no error)
        update_activity_event(event_id, status="success", duration_ms=duration_ms)


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
