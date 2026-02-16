"""Property recap and phone call MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post
from ..utils.property_resolver import resolve_property_id


# ── Helpers ──

async def generate_property_recap(property_id: int, trigger: str = "manual") -> dict:
    response = api_post(f"/property-recap/property/{property_id}/generate", params={"trigger": trigger})
    response.raise_for_status()
    return response.json()


async def get_property_recap(property_id: int) -> dict:
    response = api_get(f"/property-recap/property/{property_id}")
    response.raise_for_status()
    return response.json()


async def make_property_phone_call(property_id: int, phone_number: str, call_purpose: str = "property_update") -> dict:
    response = api_post(f"/property-recap/property/{property_id}/call", json={"phone_number": phone_number, "call_purpose": call_purpose})
    response.raise_for_status()
    return response.json()


async def call_contact_about_contract(property_id: int, contact_id: int, contract_id: int, custom_message=None) -> dict:
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
        response = api_post(f"/property-recap/property/{property_id}/call", json={
            "phone_number": contact.phone,
            "call_purpose": "specific_contract_reminder",
            "custom_context": {
                "contact_name": contact.name,
                "contract_id": contract_id,
                "contract_name": contract.name,
                "contract_status": contract.status.value,
                "custom_message": custom_message,
            },
        })
        response.raise_for_status()
        result = response.json()
        result["contact_name"] = contact.name
        result["contract_name"] = contract.name
        return result
    finally:
        db.close()


async def call_property_owner_skip_trace(property_id: int, custom_message=None) -> dict:
    from app.database import SessionLocal
    from app.models.skip_trace import SkipTrace
    from app.models.property import Property
    import json as json_mod

    db = SessionLocal()
    try:
        skip_trace = db.query(SkipTrace).filter(SkipTrace.property_id == property_id).first()
        if not skip_trace:
            raise ValueError(f"No skip trace data found for property {property_id}")
        phone_number = None
        if skip_trace.phone_numbers:
            phones = json_mod.loads(skip_trace.phone_numbers) if isinstance(skip_trace.phone_numbers, str) else skip_trace.phone_numbers
            if phones and len(phones) > 0:
                phone_number = phones[0]
        if not phone_number:
            raise ValueError("No phone number found in skip trace data")
        property_obj = db.query(Property).filter(Property.id == property_id).first()
        response = api_post(f"/property-recap/property/{property_id}/call", json={
            "phone_number": phone_number,
            "call_purpose": "skip_trace_outreach",
            "custom_context": {
                "owner_name": skip_trace.owner_name,
                "property_address": f"{property_obj.address}, {property_obj.city}, {property_obj.state}",
                "custom_message": custom_message,
            },
        })
        response.raise_for_status()
        result = response.json()
        result["owner_name"] = skip_trace.owner_name
        result["call_type"] = "skip_trace_outreach"
        return result
    finally:
        db.close()


# ── Handlers ──

async def handle_generate_property_recap(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    trigger = arguments.get("trigger", "manual")
    result = await generate_property_recap(property_id=property_id, trigger=trigger)

    recap_text = f"Recap generated for {result['property_address']} (v{result['version']}).\n\n{result['voice_summary']}"
    key_facts = result.get('recap_context', {}).get('ai_summary', {}).get('key_facts', [])
    if key_facts:
        recap_text += f"\n\nKey facts: {'; '.join(key_facts)}."
    return [TextContent(type="text", text=recap_text)]


async def handle_get_property_recap(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    result = await get_property_recap(property_id=property_id)

    recap_text = f"Recap for {result['property_address']} (v{result['version']}, updated via {result.get('last_trigger', 'unknown')}).\n\n{result['voice_summary']}"
    readiness = result.get('recap_context', {}).get('readiness')
    if readiness:
        ready = "ready to close" if readiness['is_ready_to_close'] else "not ready to close"
        recap_text += f"\n\nContracts: {readiness['completed']}/{readiness['total_required']} completed, {readiness['in_progress']} in progress, {readiness['missing']} missing — {ready}."
    return [TextContent(type="text", text=recap_text)]


async def handle_make_property_phone_call(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    phone_number = arguments["phone_number"]
    call_purpose = arguments.get("call_purpose", "property_update")
    result = await make_property_phone_call(property_id=property_id, phone_number=phone_number, call_purpose=call_purpose)

    call_text = f"Call initiated to {result['phone_number']} about {result['property_address']} ({call_purpose.replace('_', ' ')}). Call ID: {result['call_id']}, status: {result['status']}."
    return [TextContent(type="text", text=call_text)]


async def handle_call_contact_about_contract(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    contact_id = arguments["contact_id"]
    contract_id = arguments["contract_id"]
    custom_message = arguments.get("custom_message")
    result = await call_contact_about_contract(property_id=property_id, contact_id=contact_id, contract_id=contract_id, custom_message=custom_message)

    call_text = f"Calling {result['contact_name']} at {result['phone_number']} about the {result['contract_name']} for {result['property_address']}. Call ID: {result['call_id']}."
    if custom_message:
        call_text += f" Custom message: {custom_message}"
    return [TextContent(type="text", text=call_text)]


async def handle_call_property_owner_skip_trace(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    custom_message = arguments.get("custom_message")
    result = await call_property_owner_skip_trace(property_id=property_id, custom_message=custom_message)

    call_text = f"Cold calling {result['owner_name']} at {result['phone_number']} about {result['property_address']}. Call ID: {result['call_id']}."
    if custom_message:
        call_text += f" Custom message: {custom_message}"
    return [TextContent(type="text", text=call_text)]


# ── Tool Registration ──

register_tool(Tool(name="generate_property_recap", description="AI PROPERTY RECAP: Generate comprehensive AI summary of property including status, contracts, and readiness. Voice-friendly: say the address instead of the ID. Example: 'Generate a recap for 123 Main Street'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID (optional if address provided)"}, "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street')"}, "trigger": {"type": "string", "description": "What triggered this recap (manual, property_updated, contract_signed, etc.). Default: manual", "default": "manual"}}}), handle_generate_property_recap)

register_tool(Tool(name="get_property_recap", description="GET PROPERTY RECAP: Retrieve existing AI-generated property summary. Voice-friendly: say the address instead of the ID. Example: 'Get the recap for 123 Main Street'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID (optional if address provided)"}, "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street')"}}}), handle_get_property_recap)

register_tool(Tool(name="make_property_phone_call", description="MAKE PHONE CALL: Make an AI-powered phone call about a property. Voice-friendly: say the address instead of the ID. Example: 'Call +14155551234 about 123 Main Street'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID (optional if address provided)"}, "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street')"}, "phone_number": {"type": "string", "description": "Phone number to call in E.164 format (e.g., +14155551234 for US, +442071234567 for UK)"}, "call_purpose": {"type": "string", "description": "Purpose of the call", "enum": ["property_update", "contract_reminder", "closing_ready"], "default": "property_update"}}, "required": ["phone_number"]}), handle_make_property_phone_call)

register_tool(Tool(name="call_contact_about_contract", description="CALL ABOUT SPECIFIC CONTRACT: Call a contact about a specific contract. Voice-friendly: say the address instead of the property ID. Example: 'Call contact 3 about contract 10 for 123 Main Street'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID (optional if address provided)"}, "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street')"}, "contact_id": {"type": "number", "description": "Contact ID (the person to call)"}, "contract_id": {"type": "number", "description": "Contract ID (the specific contract to discuss)"}, "custom_message": {"type": "string", "description": "Optional custom message to include in the call (e.g., 'This is urgent, closing is Friday')"}}, "required": ["contact_id", "contract_id"]}), handle_call_contact_about_contract)

register_tool(Tool(name="call_property_owner_skip_trace", description="SKIP TRACE OUTREACH CALL: Call property owner from skip trace data. Voice-friendly: say the address instead of the ID. Example: 'Call the owner of 123 Main Street and ask if they want to sell'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID (optional if address provided)"}, "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street')"}, "custom_message": {"type": "string", "description": "Optional custom message (e.g., 'We have a buyer interested in your area', 'Market values are up 15% this year')"}}}), handle_call_property_owner_skip_trace)
