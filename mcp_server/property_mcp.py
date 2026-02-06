#!/usr/bin/env python3
"""
Property Management MCP Server for AI Realtor
Exposes property database operations as MCP tools

Supports two transports:
  - stdio (default): For local Claude Desktop usage
  - sse: For remote HTTP access (deployed on Fly.io)

Usage:
  python property_mcp.py                  # stdio mode
  python property_mcp.py --transport sse  # SSE mode on port 8001
  python property_mcp.py --transport sse --port 9000
"""
import argparse
import asyncio
import json
import os
import sys
import time
from typing import Any, Optional
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

# API Base URL - use env var for deployed mode, localhost for local
API_BASE_URL = os.getenv("MCP_API_BASE_URL", "http://localhost:8000")

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


async def ai_suggest_contracts_for_property(property_id: Optional[int] = None, address_query: Optional[str] = None) -> dict:
    """
    Use AI to analyze property and suggest which contracts are required vs optional.
    Returns AI-powered recommendations based on property characteristics and regulations.
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

    response = requests.post(f"{API_BASE_URL}/contracts/property/{property_id}/ai-suggest")
    response.raise_for_status()
    return response.json()


async def apply_ai_contract_suggestions(
    property_id: Optional[int] = None,
    address_query: Optional[str] = None,
    only_required: bool = True
) -> dict:
    """
    Apply AI suggestions by creating contracts for the property.
    By default, only creates contracts that AI marked as 'required'.
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

    response = requests.post(
        f"{API_BASE_URL}/contracts/property/{property_id}/ai-apply-suggestions",
        params={"only_required": only_required}
    )
    response.raise_for_status()
    return response.json()


async def mark_contract_required(
    contract_id: int,
    is_required: bool = True,
    reason: Optional[str] = None,
    required_by_date: Optional[str] = None
) -> dict:
    """
    Manually mark a contract as required or optional.
    This overrides AI suggestions and template defaults.
    """
    response = requests.patch(
        f"{API_BASE_URL}/contracts/{contract_id}/mark-required",
        params={
            "is_required": is_required,
            "reason": reason,
            "required_by_date": required_by_date
        }
    )
    response.raise_for_status()
    return response.json()


async def generate_property_recap(property_id: int, trigger: str = "manual") -> dict:
    """
    Generate or update AI recap for a property.
    The recap includes property summary, contract status, and voice-optimized content.
    """
    response = requests.post(
        f"{API_BASE_URL}/property-recap/property/{property_id}/generate",
        params={"trigger": trigger}
    )
    response.raise_for_status()
    return response.json()


async def get_property_recap(property_id: int) -> dict:
    """Get existing AI recap for a property"""
    response = requests.get(f"{API_BASE_URL}/property-recap/property/{property_id}")
    response.raise_for_status()
    return response.json()


async def make_property_phone_call(
    property_id: int,
    phone_number: str,
    call_purpose: str = "property_update"
) -> dict:
    """
    Make a phone call about a property using VAPI.
    Phone number must be in E.164 format (e.g., +14155551234).

    Call purposes:
    - property_update: General update
    - contract_reminder: Remind about pending contracts
    - closing_ready: Celebrate property ready to close
    """
    response = requests.post(
        f"{API_BASE_URL}/property-recap/property/{property_id}/call",
        json={
            "phone_number": phone_number,
            "call_purpose": call_purpose
        }
    )
    response.raise_for_status()
    return response.json()


async def call_contact_about_contract(
    property_id: int,
    contact_id: int,
    contract_id: int,
    custom_message: Optional[str] = None
) -> dict:
    """
    Call a contact about a specific contract.

    Example: "Call John about the Purchase Agreement that needs his signature"

    The AI will:
    - Reference the specific contract by name
    - Explain what's needed (signature, review, etc.)
    - Answer questions about the contract
    - Offer to resend contract link
    """
    # Get contact phone number
    from app.database import SessionLocal
    from app.models.contact import Contact
    from app.models.contract import Contract

    db = SessionLocal()
    try:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact or not contact.phone:
            raise ValueError(f"Contact {contact_id} not found or has no phone number")

        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        # Build custom call with specific contract context
        response = requests.post(
            f"{API_BASE_URL}/property-recap/property/{property_id}/call",
            json={
                "phone_number": contact.phone,
                "call_purpose": "specific_contract_reminder",
                "custom_context": {
                    "contact_name": contact.name,
                    "contract_id": contract_id,
                    "contract_name": contract.name,
                    "contract_status": contract.status.value,
                    "custom_message": custom_message
                }
            }
        )
        response.raise_for_status()

        result = response.json()
        result["contact_name"] = contact.name
        result["contract_name"] = contract.name
        return result

    finally:
        db.close()


async def call_property_owner_skip_trace(
    property_id: int,
    custom_message: Optional[str] = None
) -> dict:
    """
    Call property owner from skip trace data and ask if interested in selling.

    Example: "Call the owner of this property and ask if they're interested in selling"

    The AI will:
    - Introduce as real estate professional
    - Ask if they've considered selling
    - Discuss current market conditions
    - Answer questions about selling process
    - Not be pushy, just exploratory
    """
    from app.database import SessionLocal
    from app.models.skip_trace import SkipTrace
    from app.models.property import Property

    db = SessionLocal()
    try:
        # Get skip trace data
        skip_trace = db.query(SkipTrace).filter(
            SkipTrace.property_id == property_id
        ).first()

        if not skip_trace:
            raise ValueError(f"No skip trace data found for property {property_id}")

        # Get best phone number from skip trace
        phone_number = None
        if skip_trace.phone_numbers:
            # Parse phone numbers and pick first one
            import json
            phones = json.loads(skip_trace.phone_numbers) if isinstance(skip_trace.phone_numbers, str) else skip_trace.phone_numbers
            if phones and len(phones) > 0:
                phone_number = phones[0]

        if not phone_number:
            raise ValueError("No phone number found in skip trace data")

        property = db.query(Property).filter(Property.id == property_id).first()

        # Make skip trace outreach call
        response = requests.post(
            f"{API_BASE_URL}/property-recap/property/{property_id}/call",
            json={
                "phone_number": phone_number,
                "call_purpose": "skip_trace_outreach",
                "custom_context": {
                    "owner_name": skip_trace.owner_name,
                    "property_address": f"{property.address}, {property.city}, {property.state}",
                    "custom_message": custom_message
                }
            }
        )
        response.raise_for_status()

        result = response.json()
        result["owner_name"] = skip_trace.owner_name
        result["call_type"] = "skip_trace_outreach"
        return result

    finally:
        db.close()


async def test_webhook_configuration() -> dict:
    """Test webhook configuration and get setup instructions"""
    response = requests.get(f"{API_BASE_URL}/webhooks/docuseal/test")
    response.raise_for_status()
    return response.json()


async def smart_send_contract(
    address_query: str,
    contract_name: str,
    order: str = "preserved",
    message: Optional[str] = None,
    create_if_missing: bool = True
) -> dict:
    """
    Smart-send a contract - auto-determines who needs to sign.
    No need to specify roles - the system knows Purchase Agreement needs buyer + seller, etc.
    """
    response = requests.post(
        f"{API_BASE_URL}/contracts/voice/smart-send",
        json={
            "address_query": address_query,
            "contract_name": contract_name,
            "order": order,
            "message": message,
            "create_if_missing": create_if_missing,
        }
    )
    response.raise_for_status()
    return response.json()


async def get_signing_status(property_id: int) -> dict:
    """Get signing status for all contracts on a property."""
    response = requests.get(f"{API_BASE_URL}/contracts/property/{property_id}/signing-status")
    response.raise_for_status()
    return response.json()


async def set_deal_type(property_id: int, deal_type_name: str, clear_previous: bool = False) -> dict:
    """Set a deal type on a property and trigger the full workflow."""
    response = requests.post(
        f"{API_BASE_URL}/properties/{property_id}/set-deal-type",
        params={"deal_type_name": deal_type_name, "clear_previous": clear_previous}
    )
    response.raise_for_status()
    return response.json()


async def get_deal_status(property_id: int) -> dict:
    """Get deal progress for a property."""
    response = requests.get(f"{API_BASE_URL}/properties/{property_id}/deal-status")
    response.raise_for_status()
    return response.json()


async def list_deal_types_api() -> list:
    """List all available deal type configs."""
    response = requests.get(f"{API_BASE_URL}/deal-types/")
    response.raise_for_status()
    return response.json()


async def get_deal_type_config(name: str) -> dict:
    """Get a specific deal type config by name."""
    response = requests.get(f"{API_BASE_URL}/deal-types/{name}")
    response.raise_for_status()
    return response.json()


async def create_deal_type_config(data: dict) -> dict:
    """Create a custom deal type config."""
    response = requests.post(f"{API_BASE_URL}/deal-types/", json=data)
    response.raise_for_status()
    return response.json()


async def update_deal_type_config(name: str, data: dict) -> dict:
    """Update a deal type config."""
    response = requests.put(f"{API_BASE_URL}/deal-types/{name}", json=data)
    response.raise_for_status()
    return response.json()


async def delete_deal_type_config(name: str) -> dict:
    """Delete a custom deal type config."""
    response = requests.delete(f"{API_BASE_URL}/deal-types/{name}")
    if response.status_code == 204:
        return {"success": True, "name": name}
    response.raise_for_status()
    return response.json()


async def preview_deal_type_api(name: str, property_id: int) -> dict:
    """Preview what a deal type would trigger on a property (dry run)."""
    response = requests.post(
        f"{API_BASE_URL}/deal-types/{name}/preview",
        params={"property_id": property_id}
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
            description="Add a contact to a property. Set send_contracts=true to automatically find and send any draft contracts that need this contact's role signature. Example: 'Add Daffy Duck as the lawyer and send him the contracts'.",
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
                        "description": "Contact's email address (required if send_contracts is true)"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Contact's phone number"
                    },
                    "role": {
                        "type": "string",
                        "description": "Contact's role",
                        "enum": ["buyer", "seller", "lawyer", "attorney", "contractor", "inspector", "appraiser", "lender", "mortgage_broker", "title_company", "tenant", "landlord", "property_manager", "handyman", "plumber", "electrician", "photographer", "stager", "other"],
                        "default": "buyer"
                    },
                    "send_contracts": {
                        "type": "boolean",
                        "description": "If true, automatically find draft contracts needing this role's signature and report which are ready to send",
                        "default": False
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
            name="get_signing_status",
            description="✍️ WHO SIGNED? Voice-optimized signing status for a property. Shows who has signed, who hasn't, across ALL contracts. Perfect for 'Who still needs to sign for property 5?', 'Has John signed yet?', 'What's the signing status for 123 Main St?'. Returns natural language summary.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "Property ID to check signing status for"
                    }
                },
                "required": ["property_id"]
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
        ),
        Tool(
            name="ai_suggest_contracts",
            description="🤖 AI-POWERED: Use Claude AI to analyze a property and suggest which contracts are required vs optional. AI considers state/local regulations, property type, price range, and best practices. Returns intelligent recommendations with reasoning for each contract. Perfect for asking 'What contracts does this property need?'",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "Property ID to analyze (optional if address_query provided)"
                    },
                    "address_query": {
                        "type": "string",
                        "description": "Natural language address (voice-friendly). Examples: 'suggest contracts for one forty one throop', 'what contracts does main street need'. Handles phonetic variations."
                    }
                }
            }
        ),
        Tool(
            name="apply_ai_contract_suggestions",
            description="🤖 AI-POWERED: Apply AI suggestions by automatically creating the recommended contracts for a property. By default, only creates contracts marked as 'required' by AI analysis. This respects AI's intelligence about what's legally necessary vs nice-to-have. Perfect for 'Apply AI contract suggestions to this property'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "Property ID (optional if address_query provided)"
                    },
                    "address_query": {
                        "type": "string",
                        "description": "Natural language address (voice-friendly). Examples: 'apply suggestions to one forty one throop', 'add AI contracts to main street'. Handles phonetic variations."
                    },
                    "only_required": {
                        "type": "boolean",
                        "description": "If true, only create contracts AI marked as 'required'. If false, create both required and optional. Default: true",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="mark_contract_required",
            description="✋ MANUAL OVERRIDE: Manually mark a specific contract as required or optional for a property. This gives you full control to override AI suggestions and template defaults. Use when you know better than the automated systems. Perfect for 'Mark this contract as required' or 'This contract is optional'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_id": {
                        "type": "number",
                        "description": "Contract ID to update (required)"
                    },
                    "is_required": {
                        "type": "boolean",
                        "description": "True = required, False = optional. Default: true",
                        "default": True
                    },
                    "reason": {
                        "type": "string",
                        "description": "Optional: Reason for this requirement (e.g., 'Client specifically requested', 'State law requires')"
                    },
                    "required_by_date": {
                        "type": "string",
                        "description": "Optional: Deadline in ISO format (e.g., '2024-12-31T23:59:59Z')"
                    }
                },
                "required": ["contract_id"]
            }
        ),
        Tool(
            name="generate_property_recap",
            description="🤖 AI PROPERTY RECAP: Generate comprehensive AI summary of property including status, contracts, and readiness. Creates both detailed and voice-optimized summaries perfect for phone calls. Auto-updates whenever property changes. Use this before making calls or when you need a quick property overview.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "Property ID to generate recap for"
                    },
                    "trigger": {
                        "type": "string",
                        "description": "What triggered this recap (manual, property_updated, contract_signed, etc.). Default: manual",
                        "default": "manual"
                    }
                },
                "required": ["property_id"]
            }
        ),
        Tool(
            name="get_property_recap",
            description="📖 GET PROPERTY RECAP: Retrieve existing AI-generated property summary. Returns detailed overview, voice summary, and structured context. Faster than generate if recap already exists.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "Property ID to get recap for"
                    }
                },
                "required": ["property_id"]
            }
        ),
        Tool(
            name="make_property_phone_call",
            description="📞 MAKE PHONE CALL: Make an AI-powered phone call about a property using VAPI. The AI assistant will have full property context and can answer questions. Perfect for property updates, contract reminders, or celebrating closing readiness. Automatically generates property recap if needed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "Property ID to discuss in the call"
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "Phone number to call in E.164 format (e.g., +14155551234 for US, +442071234567 for UK)"
                    },
                    "call_purpose": {
                        "type": "string",
                        "description": "Purpose of the call",
                        "enum": ["property_update", "contract_reminder", "closing_ready"],
                        "default": "property_update"
                    }
                },
                "required": ["property_id", "phone_number"]
            }
        ),
        Tool(
            name="call_contact_about_contract",
            description="📞💼 CALL ABOUT SPECIFIC CONTRACT: Call a contact about a specific contract that needs attention. Perfect for 'Call John about the Purchase Agreement that needs his signature'. AI will reference the exact contract, explain what's needed, and offer to resend links. More targeted than general property update.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "Property ID"
                    },
                    "contact_id": {
                        "type": "number",
                        "description": "Contact ID (the person to call)"
                    },
                    "contract_id": {
                        "type": "number",
                        "description": "Contract ID (the specific contract to discuss)"
                    },
                    "custom_message": {
                        "type": "string",
                        "description": "Optional custom message to include in the call (e.g., 'This is urgent, closing is Friday')"
                    }
                },
                "required": ["property_id", "contact_id", "contract_id"]
            }
        ),
        Tool(
            name="call_property_owner_skip_trace",
            description="📞🏠 SKIP TRACE OUTREACH CALL: Call property owner (from skip trace data) and ask if they're interested in selling. Perfect for cold calling and lead generation. AI will: introduce as real estate professional, ask about interest in selling, discuss market conditions, be respectful and not pushy. Uses phone number from skip trace data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "Property ID (must have skip trace data)"
                    },
                    "custom_message": {
                        "type": "string",
                        "description": "Optional custom message (e.g., 'We have a buyer interested in your area', 'Market values are up 15% this year')"
                    }
                },
                "required": ["property_id"]
            }
        ),
        Tool(
            name="test_webhook_configuration",
            description="🔗 TEST WEBHOOK SETUP: Check DocuSeal webhook configuration status and get setup instructions. Shows webhook URL, whether secret is configured, supported events, and step-by-step setup guide for connecting DocuSeal to automatically update contracts when signed.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="set_deal_type",
            description="🏷️ SET DEAL TYPE: Set a deal type on a property to trigger a full workflow. Auto-attaches the right contracts, creates a step-by-step checklist, and flags required contact roles. Available deal types: traditional, short_sale, reo, fsbo, new_construction, wholesale, rental, commercial. When SWITCHING deal types, use clear_previous=true to remove old draft contracts and pending todos first. Example: 'Set property 5 as a short sale' or 'Change property 5 from short sale to traditional'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "Property ID to set the deal type on"
                    },
                    "deal_type": {
                        "type": "string",
                        "description": "Deal type name: traditional, short_sale, reo, fsbo, new_construction, wholesale, rental, commercial (or custom)"
                    },
                    "clear_previous": {
                        "type": "boolean",
                        "description": "If true and switching deal types, removes draft contracts and pending todos from the old deal type first. Completed/signed contracts are never removed. Default: false",
                        "default": False
                    }
                },
                "required": ["property_id", "deal_type"]
            }
        ),
        Tool(
            name="get_deal_status",
            description="📊 DEAL STATUS: Check the deal progress for a property — contracts completed vs pending, checklist items done, and missing contacts. Great for 'Is this deal on track?' or 'What's left to do for property 5?'",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "number",
                        "description": "Property ID to check deal status for"
                    }
                },
                "required": ["property_id"]
            }
        ),
        Tool(
            name="list_deal_types",
            description="📋 LIST DEAL TYPES: Show all available deal types and what each one triggers (contracts, checklist, required contacts). Useful for 'What deal types are available?' or 'What does a short sale include?'",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_deal_type_config",
            description="🔍 GET DEAL TYPE CONFIG: Get full details of a specific deal type — its contracts, required contacts, checklist items, and compliance tags. Example: 'Show me the short sale config' or 'What contracts does a wholesale deal need?'",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Deal type name (e.g., 'short_sale', 'traditional', 'rental')"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="create_deal_type_config",
            description="➕ CREATE CUSTOM DEAL TYPE: Create a new deal type with custom contracts, required contacts, and checklist. Example: '1031 Exchange' with contracts like 'Exchange Agreement' and required roles like buyer + seller + intermediary.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Unique identifier (lowercase, underscores, e.g., '1031_exchange')"
                    },
                    "display_name": {
                        "type": "string",
                        "description": "Human-readable name (e.g., '1031 Exchange')"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of this deal type"
                    },
                    "contract_templates": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Contract names to auto-attach (e.g., ['Purchase Agreement', 'Exchange Agreement'])"
                    },
                    "required_contact_roles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Required contact roles (e.g., ['buyer', 'seller', 'lender'])"
                    },
                    "checklist": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                                "due_days": {"type": "number"}
                            },
                            "required": ["title"]
                        },
                        "description": "Checklist items to auto-create as todos"
                    }
                },
                "required": ["name", "display_name"]
            }
        ),
        Tool(
            name="update_deal_type_config",
            description="✏️ UPDATE DEAL TYPE CONFIG: Change the contracts, required contacts, checklist, or other settings on a deal type. Example: 'Add Bank Authorization to the short sale contracts' or 'Remove lender from traditional required contacts'. Changes apply to future deal type applications only.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Deal type name to update (e.g., 'short_sale')"
                    },
                    "display_name": {
                        "type": "string",
                        "description": "New display name"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description"
                    },
                    "contract_templates": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Full list of contract names (replaces existing list)"
                    },
                    "required_contact_roles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Full list of required roles (replaces existing list)"
                    },
                    "checklist": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                                "due_days": {"type": "number"}
                            },
                            "required": ["title"]
                        },
                        "description": "Full checklist (replaces existing list)"
                    },
                    "is_active": {
                        "type": "boolean",
                        "description": "Enable or disable this deal type"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="delete_deal_type_config",
            description="🗑️ DELETE DEAL TYPE: Delete a custom deal type config. Cannot delete built-in deal types (traditional, short_sale, etc). Example: 'Delete the 1031 exchange deal type'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Deal type name to delete"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="preview_deal_type",
            description="👀 PREVIEW DEAL TYPE: Dry run — see what contracts, todos, and contacts would be created if you applied a deal type to a property, WITHOUT actually doing it. Example: 'Preview what a short sale would do for property 5'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Deal type name to preview"
                    },
                    "property_id": {
                        "type": "number",
                        "description": "Property ID to preview against"
                    }
                },
                "required": ["name", "property_id"]
            }
        ),
        Tool(
            name="smart_send_contract",
            description="🚀 SMART SEND: Send a contract and automatically determine who needs to sign it. No need to specify contact roles! The system knows that a Purchase Agreement needs buyer + seller, an Inspection Report needs the inspector, etc. Just say the contract name and address. Example: 'Send the purchase agreement for 123 Main St' - system auto-finds buyer and seller contacts and sends to both.",
            inputSchema={
                "type": "object",
                "properties": {
                    "address_query": {
                        "type": "string",
                        "description": "Natural language address (voice-friendly). Examples: 'one forty one throop', '123 main street', 'contract lane'. Handles phonetic variations."
                    },
                    "contract_name": {
                        "type": "string",
                        "description": "Name of the contract to send. Examples: 'Purchase Agreement', 'Inspection Report', 'Disclosure Form', 'Lease Agreement'. Fuzzy-matched to templates."
                    },
                    "order": {
                        "type": "string",
                        "description": "Signing order: 'preserved' for sequential (buyer signs first, then seller) or 'random' for parallel (all sign at once). Default: preserved",
                        "enum": ["preserved", "random"],
                        "default": "preserved"
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional custom message to include in the signing email"
                    },
                    "create_if_missing": {
                        "type": "boolean",
                        "description": "If true, auto-create the contract if it doesn't exist yet. Default: true",
                        "default": True
                    }
                },
                "required": ["address_query", "contract_name"]
            }
        ),
        # ========== ELEVENLABS VOICE AGENT TOOLS ==========
        Tool(
            name="elevenlabs_setup",
            description="Set up the ElevenLabs voice agent. Registers the MCP SSE server and creates an AI agent that can use all property management tools during voice calls. One-time setup.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="elevenlabs_call",
            description="Make an outbound phone call using the ElevenLabs voice agent. The agent can use all property tools during the call. Example: 'Call +14155551234 using ElevenLabs'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "Phone number in E.164 format (e.g., +14155551234)"
                    },
                    "custom_first_message": {
                        "type": "string",
                        "description": "Optional custom greeting for the call"
                    }
                },
                "required": ["phone_number"]
            }
        ),
        Tool(
            name="elevenlabs_status",
            description="Get the ElevenLabs voice agent status and configuration. Shows agent ID, MCP connection, and widget embed code.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
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

            if not result:
                text = "No properties found."
                if status:
                    text = f"No {status} properties found."
            else:
                text = f"Found {len(result)} property(ies):\n\n"
                for p in result:
                    price_str = f"${p['price']:,.0f}" if p.get('price') else "price not set"
                    text += f"Property {p['id']}: {p.get('address', 'N/A')}, {p.get('city', '')}, {p.get('state', '')}\n"
                    text += f"  Price: {price_str}"
                    if p.get('bedrooms') or p.get('bathrooms'):
                        text += f" | {p.get('bedrooms', '?')} bed / {p.get('bathrooms', '?')} bath"
                    if p.get('square_footage'):
                        text += f" | {p['square_footage']:,.0f} sqft"
                    text += f"\n  Status: {p.get('status', 'available')}\n\n"

            return [TextContent(type="text", text=text)]

        elif name == "get_property":
            property_id = arguments["property_id"]
            result = await get_property(property_id)

            price_str = f"${result['price']:,.0f}" if result.get('price') else "price not set"
            text = f"Property {result['id']}: {result.get('address', 'N/A')}, {result.get('city', '')}, {result.get('state', '')} {result.get('zip_code', '')}\n\n"
            text += f"Price: {price_str}\n"
            if result.get('bedrooms'):
                text += f"Bedrooms: {result['bedrooms']}\n"
            if result.get('bathrooms'):
                text += f"Bathrooms: {result['bathrooms']}\n"
            if result.get('square_footage'):
                text += f"Square footage: {result['square_footage']:,.0f}\n"
            text += f"Status: {result.get('status', 'available')}\n"
            if result.get('property_type'):
                text += f"Type: {result['property_type']}\n"

            # Include enrichment highlights if available
            enrichment = result.get('zillow_enrichment')
            if enrichment:
                if enrichment.get('zestimate'):
                    text += f"\nZestimate: ${enrichment['zestimate']:,.0f}\n"
                if enrichment.get('rent_zestimate'):
                    text += f"Rent estimate: ${enrichment['rent_zestimate']:,.0f}/month\n"
                if enrichment.get('year_built'):
                    text += f"Year built: {enrichment['year_built']}\n"

            return [TextContent(type="text", text=text)]

        elif name == "create_property":
            result = await create_property_with_address(
                address=arguments["address"],
                price=arguments["price"],
                bedrooms=arguments.get("bedrooms"),
                bathrooms=arguments.get("bathrooms"),
                agent_id=arguments.get("agent_id", 1)
            )

            # Context API returns {success, message, data: {property_id, address, city, state, price}}
            data = result.get("data", result)
            prop_id = data.get("property_id", data.get("id", "?"))
            address = data.get("address", arguments.get("address", "N/A"))
            city = data.get("city", "")
            state = data.get("state", "")
            price = data.get("price", arguments.get("price"))
            price_str = f"${price:,.0f}" if price else ""

            text = f"Property created successfully.\n\n"
            text += f"Property {prop_id}: {address}, {city}, {state}\n"
            text += f"Price: {price_str}\n"
            if arguments.get('bedrooms'):
                text += f"Bedrooms: {arguments['bedrooms']}\n"
            if arguments.get('bathrooms'):
                text += f"Bathrooms: {arguments['bathrooms']}\n"
            text += f"Status: available\n"

            return [TextContent(type="text", text=text)]

        elif name == "delete_property":
            property_id = arguments["property_id"]
            result = await delete_property(property_id)

            text = f"Property {property_id} deleted successfully."
            if result.get('address'):
                text = f"Property {property_id} at {result['address']} has been deleted."

            return [TextContent(type="text", text=text)]

        elif name == "enrich_property":
            property_id = arguments["property_id"]
            result = await enrich_property(property_id)

            text = f"Property {property_id} enriched with Zillow data.\n\n"
            enrichment = result.get("enrichment", result)
            if enrichment.get('zestimate'):
                text += f"Zestimate: ${enrichment['zestimate']:,.0f}\n"
            if enrichment.get('rent_zestimate'):
                text += f"Rent estimate: ${enrichment['rent_zestimate']:,.0f}/month\n"
            if enrichment.get('year_built'):
                text += f"Year built: {enrichment['year_built']}\n"
            if enrichment.get('bedrooms'):
                text += f"Bedrooms: {enrichment['bedrooms']}\n"
            if enrichment.get('bathrooms'):
                text += f"Bathrooms: {enrichment['bathrooms']}\n"
            if enrichment.get('living_area'):
                text += f"Living area: {enrichment['living_area']:,.0f} sqft\n"
            if enrichment.get('lot_size'):
                text += f"Lot size: {enrichment['lot_size']}\n"
            if enrichment.get('home_type'):
                text += f"Home type: {enrichment['home_type']}\n"
            photos = enrichment.get('photos', [])
            if photos:
                text += f"Photos: {len(photos)} available\n"
            schools = enrichment.get('schools', [])
            if schools:
                text += f"\nNearby schools:\n"
                for s in schools[:3]:
                    rating = f" (rating: {s['rating']}/10)" if s.get('rating') else ""
                    text += f"  - {s.get('name', 'Unknown')}{rating}\n"

            return [TextContent(type="text", text=text)]

        elif name == "skip_trace_property":
            property_id = arguments["property_id"]
            result = await skip_trace_property(property_id)

            text = f"Skip trace completed for property {property_id}.\n\n"
            trace = result.get("skip_trace", result)
            if trace.get('owner_name'):
                text += f"Owner: {trace['owner_name']}\n"
            phones = trace.get('phone_numbers', [])
            if phones:
                text += f"Phone numbers: {', '.join(phones)}\n"
            emails = trace.get('email_addresses', [])
            if emails:
                text += f"Email addresses: {', '.join(emails)}\n"
            if trace.get('mailing_address'):
                text += f"Mailing address: {trace['mailing_address']}\n"
            relatives = trace.get('relatives', [])
            if relatives:
                text += f"Relatives: {', '.join(relatives)}\n"

            return [TextContent(type="text", text=text)]

        elif name == "add_contact":
            result = await add_contact_to_property(
                property_id=arguments["property_id"],
                name=arguments["name"],
                email=arguments.get("email"),
                phone=arguments.get("phone"),
                role=arguments.get("role", "buyer")
            )

            contact_name = result.get("name", arguments["name"])
            contact_role = result.get("role", arguments.get("role", "buyer")).replace("_", " ")
            output = f"Added {contact_name} as {contact_role} for property {arguments['property_id']}.\n"

            # If send_contracts requested, find matching draft contracts
            if arguments.get("send_contracts"):
                contact_id = result.get("id")
                if contact_id:
                    try:
                        send_response = requests.post(
                            f"{API_BASE_URL}/contacts/{contact_id}/send-pending-contracts"
                        )
                        send_response.raise_for_status()
                        send_result = send_response.json()

                        matched = send_result.get("matched_contracts", [])
                        if matched:
                            output += f"\n📋 Contract matching:\n"
                            for m in matched:
                                status = "✅ Ready to send" if m["ready_to_send"] else f"⚠️ Missing: {', '.join(m['missing_roles'])}"
                                signers = ", ".join(s["name"] for s in m["found_signers"])
                                output += f"  • {m['contract_name']}: {status}\n"
                                if m["found_signers"]:
                                    output += f"    Signers: {signers}\n"
                        else:
                            output += f"\nNo draft contracts need a {contact_role}'s signature on this property."

                        output += f"\n{send_result.get('voice_summary', '')}"
                    except Exception as e:
                        output += f"\nCouldn't check contracts: {str(e)}"
                else:
                    output += "\nCouldn't check contracts: contact ID not returned."

            return [TextContent(
                type="text",
                text=output
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
                text=f"Notification sent to TV display. Title: {arguments['title']}, Message: {arguments['message']}"
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
                    text=summary                )]
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
                text=f"Contract '{arguments.get('contract_name', 'Purchase Agreement')}' sent for signing to contact {arguments['contact_id']} for property {arguments['property_id']}."
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
                text=status_text            )]

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
                    text=summary                )]
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
                text=voice_text            )]

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
                text=voice_text            )]

        elif name == "get_signing_status":
            property_id = arguments["property_id"]
            result = await get_signing_status(property_id=property_id)

            # Voice summary is already included
            signing_text = f"✍️ SIGNING STATUS\n\n"
            signing_text += f"Property: {result.get('property_address', 'Unknown')}\n"
            signing_text += f"🎤 {result.get('voice_summary', '')}\n\n"

            signing_text += f"📊 TOTALS: {result.get('signed', 0)}/{result.get('total_signers', 0)} signed\n\n"

            for contract in result.get('contracts', []):
                signing_text += f"📝 {contract['contract_name']} ({contract['contract_status']})\n"
                for signer in contract.get('signers', []):
                    status_icon = "✅" if signer['status'] == 'completed' else "⏳" if signer['status'] == 'pending' else "👀" if signer['status'] == 'opened' else "❌"
                    signing_text += f"  {status_icon} {signer['name']} ({signer['role']}) - {signer['status']}\n"
                if not contract.get('signers'):
                    signing_text += f"  (no signers assigned yet)\n"
                signing_text += "\n"

            if result.get('pending_names'):
                signing_text += f"⏳ Still waiting on: {', '.join(result['pending_names'])}\n"
            elif result.get('all_signed'):
                signing_text += f"🎉 All signers have completed!\n"

            return [TextContent(
                type="text",
                text=signing_text            )]

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
                text=report            )]

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
                text=voice_text            )]

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
                text=contracts_text            )]

        elif name == "ai_suggest_contracts":
            property_id = arguments.get("property_id")
            address_query = arguments.get("address_query")
            result = await ai_suggest_contracts_for_property(property_id=property_id, address_query=address_query)

            # Format AI suggestions
            ai_text = f"🤖 AI CONTRACT SUGGESTIONS\n\n"
            ai_text += f"Property: {result.get('property_address', 'Unknown')}\n"
            ai_text += f"Total Suggested: {result.get('total_suggested', 0)}\n\n"

            # Required contracts
            required = result.get('required_contracts', [])
            if required:
                ai_text += f"✅ REQUIRED CONTRACTS ({len(required)}):\n"
                for contract in required:
                    ai_text += f"  • {contract['name']}\n"
                    ai_text += f"    Reason: {contract.get('reason', 'N/A')}\n\n"

            # Optional contracts
            optional = result.get('optional_contracts', [])
            if optional:
                ai_text += f"ℹ️  OPTIONAL CONTRACTS ({len(optional)}):\n"
                for contract in optional:
                    ai_text += f"  • {contract['name']}\n"
                    ai_text += f"    Reason: {contract.get('reason', 'N/A')}\n\n"

            # AI summary
            if result.get('summary'):
                ai_text += f"📊 AI ANALYSIS:\n{result['summary']}\n"

            return [TextContent(
                type="text",
                text=ai_text            )]

        elif name == "apply_ai_contract_suggestions":
            property_id = arguments.get("property_id")
            address_query = arguments.get("address_query")
            only_required = arguments.get("only_required", True)
            result = await apply_ai_contract_suggestions(
                property_id=property_id,
                address_query=address_query,
                only_required=only_required
            )

            # Format result
            created_count = result.get('contracts_created', 0)
            apply_text = f"🤖 AI SUGGESTIONS APPLIED\n\n"
            apply_text += f"Property: {result.get('property_address', 'Unknown')}\n"
            apply_text += f"Contracts Created: {created_count}\n"
            apply_text += f"Mode: {'Required only' if only_required else 'Required + Optional'}\n\n"

            if created_count > 0:
                apply_text += f"📝 CREATED CONTRACTS:\n"
                for contract in result.get('contracts', []):
                    apply_text += f"  • {contract['name']} (ID: {contract['id']})\n"
                    if contract.get('requirement_reason'):
                        apply_text += f"    AI Reason: {contract['requirement_reason']}\n"
            else:
                apply_text += "ℹ️ No new contracts created (all suggested contracts already exist)\n"

            return [TextContent(
                type="text",
                text=apply_text            )]

        elif name == "mark_contract_required":
            contract_id = arguments["contract_id"]
            is_required = arguments.get("is_required", True)
            reason = arguments.get("reason")
            required_by_date = arguments.get("required_by_date")
            result = await mark_contract_required(
                contract_id=contract_id,
                is_required=is_required,
                reason=reason,
                required_by_date=required_by_date
            )

            # Format result
            status = "REQUIRED" if is_required else "OPTIONAL"
            override_text = f"✋ MANUAL OVERRIDE APPLIED\n\n"
            override_text += f"Contract ID: {contract_id}\n"
            override_text += f"Contract: {result.get('contract_name', 'Unknown')}\n"
            override_text += f"Status: {status}\n"

            if reason:
                override_text += f"Reason: {reason}\n"

            if required_by_date:
                override_text += f"Required By: {required_by_date}\n"

            override_text += f"\nProperty: {result.get('property_address', 'Unknown')}\n"
            override_text += f"Source: MANUAL (user override)\n"

            return [TextContent(
                type="text",
                text=override_text            )]

        elif name == "generate_property_recap":
            property_id = arguments["property_id"]
            trigger = arguments.get("trigger", "manual")
            result = await generate_property_recap(property_id=property_id, trigger=trigger)

            # Format recap
            recap_text = f"🤖 AI PROPERTY RECAP GENERATED\n\n"
            recap_text += f"Property: {result['property_address']}\n"
            recap_text += f"Version: {result['version']}\n"
            recap_text += f"Trigger: {result.get('last_trigger', 'unknown')}\n\n"

            recap_text += f"📝 DETAILED SUMMARY:\n{result['recap_text']}\n\n"
            recap_text += f"🎤 VOICE SUMMARY (for calls):\n{result['voice_summary']}\n\n"

            # Show key facts from structured context
            if result.get('recap_context', {}).get('ai_summary', {}).get('key_facts'):
                recap_text += f"🔑 KEY FACTS:\n"
                for fact in result['recap_context']['ai_summary']['key_facts']:
                    recap_text += f"  • {fact}\n"

            return [TextContent(
                type="text",
                text=recap_text            )]

        elif name == "get_property_recap":
            property_id = arguments["property_id"]
            result = await get_property_recap(property_id=property_id)

            # Format recap
            recap_text = f"📖 EXISTING PROPERTY RECAP\n\n"
            recap_text += f"Property: {result['property_address']}\n"
            recap_text += f"Version: {result['version']}\n"
            recap_text += f"Last Updated: {result.get('last_trigger', 'unknown')}\n\n"

            recap_text += f"📝 SUMMARY:\n{result['voice_summary']}\n\n"

            # Show readiness info
            if result.get('recap_context', {}).get('readiness'):
                readiness = result['recap_context']['readiness']
                recap_text += f"📊 CONTRACT STATUS:\n"
                recap_text += f"  Ready to Close: {'YES' if readiness['is_ready_to_close'] else 'NO'}\n"
                recap_text += f"  Completed: {readiness['completed']}/{readiness['total_required']}\n"
                recap_text += f"  In Progress: {readiness['in_progress']}\n"
                recap_text += f"  Missing: {readiness['missing']}\n"

            return [TextContent(
                type="text",
                text=recap_text            )]

        elif name == "make_property_phone_call":
            property_id = arguments["property_id"]
            phone_number = arguments["phone_number"]
            call_purpose = arguments.get("call_purpose", "property_update")
            result = await make_property_phone_call(
                property_id=property_id,
                phone_number=phone_number,
                call_purpose=call_purpose
            )

            # Format call result
            call_text = f"📞 PHONE CALL INITIATED\n\n"
            call_text += f"Property: {result['property_address']}\n"
            call_text += f"Phone Number: {result['phone_number']}\n"
            call_text += f"Call Purpose: {result['call_purpose']}\n"
            call_text += f"Call ID: {result['call_id']}\n"
            call_text += f"Status: {result['status']}\n\n"

            call_text += f"✅ {result['message']}\n\n"

            call_text += f"The AI assistant will:\n"
            if call_purpose == "property_update":
                call_text += "  • Provide comprehensive property update\n"
                call_text += "  • Answer questions about the property\n"
                call_text += "  • Offer to send more info via email\n"
            elif call_purpose == "contract_reminder":
                call_text += "  • Remind about pending contracts\n"
                call_text += "  • Explain what needs attention\n"
                call_text += "  • Offer to resend contract links\n"
            elif call_purpose == "closing_ready":
                call_text += "  • Celebrate that property is ready to close\n"
                call_text += "  • Confirm all contracts are complete\n"
                call_text += "  • Discuss next steps\n"

            call_text += f"\nUse /call/{result['call_id']}/status to check call status\n"

            return [TextContent(
                type="text",
                text=call_text            )]

        elif name == "call_contact_about_contract":
            property_id = arguments["property_id"]
            contact_id = arguments["contact_id"]
            contract_id = arguments["contract_id"]
            custom_message = arguments.get("custom_message")

            result = await call_contact_about_contract(
                property_id=property_id,
                contact_id=contact_id,
                contract_id=contract_id,
                custom_message=custom_message
            )

            # Format result
            call_text = f"📞💼 CALLING CONTACT ABOUT CONTRACT\n\n"
            call_text += f"Property: {result['property_address']}\n"
            call_text += f"Contact: {result['contact_name']}\n"
            call_text += f"Contract: {result['contract_name']}\n"
            call_text += f"Phone: {result['phone_number']}\n"
            call_text += f"Call ID: {result['call_id']}\n\n"

            if custom_message:
                call_text += f"📝 Custom Message:\n{custom_message}\n\n"

            call_text += f"✅ {result['message']}\n\n"

            call_text += f"The AI will:\n"
            call_text += f"  • Greet {result['contact_name']} by name\n"
            call_text += f"  • Remind about the {result['contract_name']}\n"
            call_text += f"  • Explain what's needed (signature, review, etc.)\n"
            call_text += f"  • Answer questions about the contract\n"
            call_text += f"  • Offer to resend contract link\n"

            return [TextContent(
                type="text",
                text=call_text            )]

        elif name == "call_property_owner_skip_trace":
            property_id = arguments["property_id"]
            custom_message = arguments.get("custom_message")

            result = await call_property_owner_skip_trace(
                property_id=property_id,
                custom_message=custom_message
            )

            # Format result
            call_text = f"📞🏠 SKIP TRACE OUTREACH CALL INITIATED\n\n"
            call_text += f"Property: {result['property_address']}\n"
            call_text += f"Owner: {result['owner_name']}\n"
            call_text += f"Phone: {result['phone_number']}\n"
            call_text += f"Call ID: {result['call_id']}\n"
            call_text += f"Call Type: Cold Call / Lead Generation\n\n"

            if custom_message:
                call_text += f"📝 Custom Message:\n{custom_message}\n\n"

            call_text += f"✅ {result['message']}\n\n"

            call_text += f"⚠️ COLD CALL - AI will:\n"
            call_text += f"  • Introduce as real estate professional\n"
            call_text += f"  • Ask if {result['owner_name']} has considered selling\n"
            call_text += f"  • Discuss current favorable market conditions\n"
            call_text += f"  • Offer no-obligation market analysis\n"
            call_text += f"  • Answer questions about selling process\n"
            call_text += f"  • Be respectful and not pushy\n"
            call_text += f"  • Keep call under 2-3 minutes unless they engage\n\n"

            call_text += f"📊 This is for lead generation/skip trace outreach\n"

            return [TextContent(
                type="text",
                text=call_text            )]

        elif name == "smart_send_contract":
            address_query = arguments["address_query"]
            contract_name = arguments["contract_name"]
            order = arguments.get("order", "preserved")
            message = arguments.get("message")
            create_if_missing = arguments.get("create_if_missing", True)

            result = await smart_send_contract(
                address_query=address_query,
                contract_name=contract_name,
                order=order,
                message=message,
                create_if_missing=create_if_missing,
            )

            # Format result
            smart_text = f"🚀 SMART SEND COMPLETE\n\n"
            smart_text += f"📝 Contract: {result['contract_name']}\n"
            smart_text += f"🏠 Property: {result['property_address']}\n\n"

            smart_text += f"✅ {result['voice_confirmation']}\n\n"

            if result.get('submitters'):
                smart_text += f"📋 SIGNERS ({len(result['submitters'])}):\n"
                for s in result['submitters']:
                    smart_text += f"  • {s['name']} ({s['role']}) - {s['email']}\n"

            if result.get('missing_roles'):
                smart_text += f"\n⚠️ MISSING ROLES: {', '.join(result['missing_roles'])}\n"

            if result.get('docuseal_url'):
                smart_text += f"\n🔗 DocuSeal URL: {result['docuseal_url']}\n"

            return [TextContent(
                type="text",
                text=smart_text            )]

        elif name == "set_deal_type":
            property_id = arguments["property_id"]
            deal_type_name = arguments["deal_type"]
            clear_previous = arguments.get("clear_previous", False)
            result = await set_deal_type(
                property_id=property_id,
                deal_type_name=deal_type_name,
                clear_previous=clear_previous,
            )

            deal_text = f"🏷️ DEAL TYPE SET\n\n"
            deal_text += f"Property: {result.get('property_address', 'Unknown')}\n"
            deal_text += f"Deal Type: {result.get('deal_type', deal_type_name)}\n\n"

            # Show removed items if switching
            if result.get('contracts_removed', 0) > 0:
                deal_text += f"🗑️ Removed {result['contracts_removed']} old contract(s): {', '.join(result.get('contracts_removed_names', []))}\n"
            if result.get('todos_removed', 0) > 0:
                deal_text += f"🗑️ Removed {result['todos_removed']} old todo(s): {', '.join(result.get('todos_removed_titles', []))}\n"
            if result.get('contracts_removed', 0) > 0 or result.get('todos_removed', 0) > 0:
                deal_text += "\n"

            deal_text += f"📝 Contracts Attached: {result.get('contracts_attached', 0)}\n"
            for name_c in result.get('contract_names', []):
                deal_text += f"  • {name_c}\n"

            deal_text += f"\n✅ Checklist Items Created: {result.get('todos_created', 0)}\n"
            for title in result.get('todo_titles', []):
                deal_text += f"  • {title}\n"

            missing = result.get('missing_contacts', [])
            if missing:
                deal_text += f"\n⚠️ Missing Required Contacts: {', '.join(missing)}\n"
                deal_text += "Add these contacts to proceed with the deal.\n"
            else:
                deal_text += f"\n✅ All required contacts are present.\n"

            return [TextContent(
                type="text",
                text=deal_text            )]

        elif name == "get_deal_status":
            property_id = arguments["property_id"]
            result = await get_deal_status(property_id=property_id)

            status_text = f"📊 DEAL STATUS\n\n"
            status_text += f"Property: {result.get('property_address', 'Unknown')}\n"
            deal_type_display = result.get('deal_type')
            if not deal_type_display:
                status_text += "No deal type set for this property.\n"
                return [TextContent(type="text", text=status_text)]

            status_text += f"Deal Type: {deal_type_display}\n\n"

            contracts = result.get('contracts', {})
            status_text += f"📝 CONTRACTS: {contracts.get('completed', 0)}/{contracts.get('total', 0)} completed\n"
            for n in contracts.get('pending_names', []):
                status_text += f"  ⏳ {n}\n"
            for n in contracts.get('completed_names', []):
                status_text += f"  ✅ {n}\n"

            checklist = result.get('checklist', {})
            status_text += f"\n✅ CHECKLIST: {checklist.get('completed', 0)}/{checklist.get('total', 0)} completed\n"
            for item in checklist.get('pending_items', []):
                status_text += f"  ⏳ {item['title']} ({item['priority']})\n"

            contacts_info = result.get('contacts', {})
            missing = contacts_info.get('missing_roles', [])
            if missing:
                status_text += f"\n⚠️ Missing Contacts: {', '.join(missing)}\n"
            else:
                status_text += f"\n✅ All required contacts present\n"

            status_text += f"\n{'🎉 READY TO CLOSE!' if result.get('ready_to_close') else '⏳ Not ready to close yet.'}\n"

            return [TextContent(
                type="text",
                text=status_text            )]

        elif name == "list_deal_types":
            result = await list_deal_types_api()

            types_text = f"📋 AVAILABLE DEAL TYPES ({len(result)})\n\n"
            for dt in result:
                types_text += f"🏷️ {dt['display_name']} ({dt['name']})\n"
                if dt.get('description'):
                    types_text += f"   {dt['description']}\n"
                if dt.get('contract_templates'):
                    types_text += f"   Contracts: {', '.join(dt['contract_templates'])}\n"
                if dt.get('required_contact_roles'):
                    types_text += f"   Required Contacts: {', '.join(dt['required_contact_roles'])}\n"
                checklist = dt.get('checklist', [])
                if checklist:
                    types_text += f"   Checklist: {len(checklist)} items\n"
                types_text += "\n"

            return [TextContent(
                type="text",
                text=types_text            )]

        elif name == "get_deal_type_config":
            dt_name = arguments["name"]
            result = await get_deal_type_config(dt_name)

            config_text = f"🔍 DEAL TYPE CONFIG: {result['display_name']}\n\n"
            if result.get('description'):
                config_text += f"{result['description']}\n\n"
            config_text += f"Name: {result['name']}\n"
            config_text += f"Built-in: {'Yes' if result.get('is_builtin') else 'No'}\n"
            config_text += f"Active: {'Yes' if result.get('is_active') else 'No'}\n\n"

            if result.get('contract_templates'):
                config_text += f"📝 Contracts ({len(result['contract_templates'])}):\n"
                for ct in result['contract_templates']:
                    config_text += f"  • {ct}\n"

            if result.get('required_contact_roles'):
                config_text += f"\n👥 Required Contacts: {', '.join(result['required_contact_roles'])}\n"

            if result.get('checklist'):
                config_text += f"\n✅ Checklist ({len(result['checklist'])} items):\n"
                for item in result['checklist']:
                    priority = item.get('priority', 'medium')
                    config_text += f"  • {item['title']} ({priority})\n"
                    if item.get('description'):
                        config_text += f"    {item['description']}\n"

            if result.get('compliance_tags'):
                config_text += f"\n🏛️ Compliance Tags: {', '.join(result['compliance_tags'])}\n"

            return [TextContent(
                type="text",
                text=config_text            )]

        elif name == "create_deal_type_config":
            data = {
                "name": arguments["name"],
                "display_name": arguments["display_name"],
            }
            if arguments.get("description"):
                data["description"] = arguments["description"]
            if arguments.get("contract_templates"):
                data["contract_templates"] = arguments["contract_templates"]
            if arguments.get("required_contact_roles"):
                data["required_contact_roles"] = arguments["required_contact_roles"]
            if arguments.get("checklist"):
                data["checklist"] = arguments["checklist"]

            result = await create_deal_type_config(data)

            create_text = f"➕ DEAL TYPE CREATED: {result['display_name']}\n\n"
            create_text += f"Name: {result['name']}\n"
            if result.get('contract_templates'):
                create_text += f"Contracts: {', '.join(result['contract_templates'])}\n"
            if result.get('required_contact_roles'):
                create_text += f"Required Contacts: {', '.join(result['required_contact_roles'])}\n"
            if result.get('checklist'):
                create_text += f"Checklist: {len(result['checklist'])} items\n"
            create_text += f"\nYou can now use 'set_deal_type' to apply it to a property.\n"

            return [TextContent(
                type="text",
                text=create_text            )]

        elif name == "update_deal_type_config":
            dt_name = arguments.pop("name")
            # Only send fields that were provided
            update_data = {k: v for k, v in arguments.items() if v is not None}

            result = await update_deal_type_config(dt_name, update_data)

            update_text = f"✏️ DEAL TYPE UPDATED: {result['display_name']}\n\n"
            update_text += f"Name: {result['name']}\n"
            if result.get('contract_templates'):
                update_text += f"Contracts: {', '.join(result['contract_templates'])}\n"
            if result.get('required_contact_roles'):
                update_text += f"Required Contacts: {', '.join(result['required_contact_roles'])}\n"
            if result.get('checklist'):
                update_text += f"Checklist: {len(result['checklist'])} items\n"
            update_text += f"\nNote: Changes apply to future deal type applications only.\n"
            update_text += f"To update an existing property, re-apply with set_deal_type (clear_previous=true).\n"

            return [TextContent(
                type="text",
                text=update_text            )]

        elif name == "delete_deal_type_config":
            dt_name = arguments["name"]
            result = await delete_deal_type_config(dt_name)

            return [TextContent(
                type="text",
                text=f"🗑️ Deal type '{dt_name}' deleted successfully."
            )]

        elif name == "preview_deal_type":
            dt_name = arguments["name"]
            property_id = arguments["property_id"]
            result = await preview_deal_type_api(dt_name, property_id)

            preview_text = f"👀 PREVIEW: {result.get('deal_type', dt_name)} on Property {property_id}\n\n"
            preview_text += f"Property: {result.get('property_address', 'Unknown')}\n\n"

            would_create = result.get('would_create_contracts', [])
            would_skip = result.get('would_skip_contracts', [])
            if would_create:
                preview_text += f"📝 Would CREATE {len(would_create)} contract(s):\n"
                for c in would_create:
                    preview_text += f"  + {c}\n"
            if would_skip:
                preview_text += f"⏭️ Would SKIP {len(would_skip)} (already exist):\n"
                for c in would_skip:
                    preview_text += f"  - {c}\n"

            would_create_todos = result.get('would_create_todos', [])
            would_skip_todos = result.get('would_skip_todos', [])
            if would_create_todos:
                preview_text += f"\n✅ Would CREATE {len(would_create_todos)} checklist item(s):\n"
                for t in would_create_todos:
                    preview_text += f"  + {t.get('title', t)}\n"
            if would_skip_todos:
                preview_text += f"⏭️ Would SKIP {len(would_skip_todos)} (already exist):\n"
                for t in would_skip_todos:
                    preview_text += f"  - {t.get('title', t)}\n"

            missing_roles = result.get('missing_contact_roles', [])
            present_roles = result.get('present_contact_roles', [])
            if missing_roles:
                preview_text += f"\n⚠️ Missing contacts: {', '.join(missing_roles)}\n"
            if present_roles:
                preview_text += f"✅ Present contacts: {', '.join(present_roles)}\n"

            preview_text += f"\nThis is a dry run — nothing was changed.\n"

            return [TextContent(
                type="text",
                text=preview_text            )]

        elif name == "test_webhook_configuration":
            result = await test_webhook_configuration()

            # Format result
            webhook_text = f"🔗 WEBHOOK CONFIGURATION STATUS\n\n"
            webhook_text += f"Webhook URL: {result['webhook_url']}\n"
            webhook_text += f"Secret Configured: {'✅ YES' if result['webhook_secret_configured'] else '⚠️ NO'}\n\n"

            webhook_text += f"📋 SUPPORTED EVENTS:\n"
            for event in result['supported_events']:
                webhook_text += f"  • {event}\n"

            webhook_text += f"\n📝 SETUP INSTRUCTIONS:\n"
            for step_num, instruction in result['instructions'].items():
                webhook_text += f"  {step_num}. {instruction}\n"

            if not result['webhook_secret_configured']:
                webhook_text += f"\n⚠️ WARNING: Webhook secret not configured! Set DOCUSEAL_WEBHOOK_SECRET environment variable for security.\n"

            return [TextContent(
                type="text",
                text=webhook_text            )]

        # ========== ELEVENLABS VOICE AGENT HANDLERS ==========
        elif name == "elevenlabs_setup":
            response = requests.post(f"{API_BASE_URL}/elevenlabs/setup")
            response.raise_for_status()
            result = response.json()

            agent_info = result.get("agent", {})
            mcp_info = result.get("mcp_server", {})

            output = f"🎙️ ELEVENLABS VOICE AGENT SET UP\n\n"
            output += f"Agent ID: {agent_info.get('agent_id', 'N/A')}\n"
            output += f"LLM: {agent_info.get('llm', 'N/A')}\n"
            output += f"MCP Server: {mcp_info.get('url', 'N/A')}\n"
            output += f"Status: {agent_info.get('status', 'N/A')}\n\n"
            output += f"Widget HTML:\n{result.get('widget_html', 'N/A')}\n"
            output += f"\nThe agent now has access to all property management tools via MCP."

            return [TextContent(type="text", text=output)]

        elif name == "elevenlabs_call":
            payload = {"phone_number": arguments["phone_number"]}
            if arguments.get("custom_first_message"):
                payload["custom_first_message"] = arguments["custom_first_message"]

            response = requests.post(f"{API_BASE_URL}/elevenlabs/call", json=payload)
            response.raise_for_status()
            result = response.json()

            output = f"📞 ELEVENLABS CALL INITIATED\n\n"
            output += f"Call ID: {result.get('call_id', 'N/A')}\n"
            output += f"To: {result.get('to_number', 'N/A')}\n"
            output += f"Status: {result.get('status', 'N/A')}\n"
            output += f"Agent: {result.get('agent_id', 'N/A')}\n"

            return [TextContent(type="text", text=output)]

        elif name == "elevenlabs_status":
            response = requests.get(f"{API_BASE_URL}/elevenlabs/agent")
            response.raise_for_status()
            result = response.json()

            if result.get("error"):
                return [TextContent(type="text", text=f"⚠️ {result['error']}")]

            output = f"🎙️ ELEVENLABS AGENT STATUS\n\n"
            output += f"Agent ID: {result.get('agent_id', 'N/A')}\n"
            output += f"Name: {result.get('name', 'N/A')}\n"
            output += f"Status: {result.get('status', 'N/A')}\n"
            output += f"MCP Server: {result.get('mcp_server_id', 'N/A')}\n"
            output += f"MCP URL: {result.get('mcp_sse_url', 'N/A')}\n"

            # Get widget info
            widget_response = requests.get(f"{API_BASE_URL}/elevenlabs/widget")
            if widget_response.ok:
                widget = widget_response.json()
                output += f"\nWidget HTML:\n{widget.get('embed_html', 'N/A')}\n"

            return [TextContent(type="text", text=output)]

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


async def main_stdio():
    """Run the MCP server over stdio (for Claude Desktop)"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main_sse(port: int = 8001):
    """Run the MCP server over SSE (for remote HTTP access)"""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.responses import JSONResponse
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    import uvicorn

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    async def handle_messages(request):
        await sse.handle_post_message(
            request.scope, request.receive, request._send
        )

    async def health(request):
        return JSONResponse({"status": "ok", "server": "property-management-mcp", "transport": "sse"})

    starlette_app = Starlette(
        routes=[
            Route("/health", health),
            Route("/sse", handle_sse),
            Route("/messages/", handle_messages, methods=["POST"]),
        ],
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            ),
        ],
    )

    print(f"MCP SSE server running on http://0.0.0.0:{port}")
    print(f"  SSE endpoint: http://0.0.0.0:{port}/sse")
    print(f"  Health check: http://0.0.0.0:{port}/health")
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Property Management MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport to use (default: stdio)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_SSE_PORT", "8001")),
        help="Port for SSE transport (default: 8001)"
    )
    args = parser.parse_args()

    if args.transport == "sse":
        main_sse(args.port)
    else:
        asyncio.run(main_stdio())
