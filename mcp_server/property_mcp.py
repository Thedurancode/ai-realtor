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
                text=ai_text + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
            )]

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
                text=apply_text + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
            )]

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
                text=override_text + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
            )]

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
                text=recap_text + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
            )]

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
                text=recap_text + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
            )]

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
                text=call_text + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
            )]

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
                text=call_text + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
            )]

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
                text=call_text + f"\n\nFull JSON:\n{json.dumps(result, indent=2)}"
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
