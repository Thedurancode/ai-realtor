"""Contract management MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post
from ..utils.property_resolver import resolve_property_id
from ..utils.voice import normalize_voice_query


# ── Helpers ──

async def send_contract(property_id, contact_id, contract_name="Purchase Agreement", docuseal_template_id=None):
    response = api_post("/contracts/", json={"property_id": property_id, "contact_id": contact_id, "name": contract_name, "docuseal_template_id": docuseal_template_id or "1"})
    response.raise_for_status()
    contract = response.json()
    response = api_post(f"/contracts/{contract['id']}/send-to-contact", json={"contact_id": contact_id})
    response.raise_for_status()
    return response.json()


async def check_contract_status(contract_id=None, address_query=None):
    if address_query:
        contracts = await list_contracts(address_query=address_query)
        if not contracts or len(contracts) == 0:
            raise ValueError(f"No contracts found for address: {address_query}")
        return await check_contract_status(contract_id=contracts[0]['id'])
    if not contract_id:
        raise ValueError("Either contract_id or address_query must be provided")
    response = api_get(f"/contracts/{contract_id}/status", params={"refresh": "true"})
    response.raise_for_status()
    return response.json()


async def list_contracts(property_id=None, address_query=None):
    if address_query:
        from app.database import SessionLocal
        from app.models.property import Property
        from sqlalchemy import func, or_
        db = SessionLocal()
        try:
            query_variations = normalize_voice_query(address_query)
            properties = db.query(Property).filter(or_(*[func.lower(Property.address).contains(var) for var in query_variations])).all()
            if not properties:
                from difflib import get_close_matches
                all_addresses = [p.address.lower() for p in db.query(Property).limit(100).all()]
                matches = get_close_matches(query_variations[0], all_addresses, n=3, cutoff=0.6)
                if matches:
                    raise ValueError(f"No exact match for '{address_query}'.\nDid you mean: {', '.join(matches)}?")
                raise ValueError(f"No property found matching address: {address_query}")
            property_id = properties[0].id
        finally:
            db.close()
    if property_id:
        url = f"/contracts/property/{property_id}"
    else:
        url = "/contracts/"
    response = api_get(url)
    response.raise_for_status()
    return response.json()


async def list_contracts_voice(address_query):
    contracts = await list_contracts(address_query=address_query)
    if not contracts or len(contracts) == 0:
        return {"voice_response": f"No contracts found for {address_query}.", "contracts": [], "count": 0}
    from app.database import SessionLocal
    from app.models.property import Property
    from sqlalchemy import func, or_
    db = SessionLocal()
    try:
        query_variations = normalize_voice_query(address_query)
        property_obj = db.query(Property).filter(or_(*[func.lower(Property.address).contains(var) for var in query_variations])).first()
        property_address = property_obj.address if property_obj else address_query
    finally:
        db.close()
    count = len(contracts)
    if count == 1:
        contract = contracts[0]
        status = contract['status'].replace('_', ' ')
        voice_response = f"Found one contract for {property_address}. It's a {contract['name']} with status {status}."
    else:
        status_counts = {}
        for c in contracts:
            s = c['status']
            status_counts[s] = status_counts.get(s, 0) + 1
        status_summary = ', '.join([f"{cnt} {st.replace('_', ' ')}" for st, cnt in status_counts.items()])
        voice_response = f"Found {count} contracts for {property_address}. Status breakdown: {status_summary}."
    return {"voice_response": voice_response, "contracts": contracts, "count": count, "address": property_address}


async def check_contract_status_voice(address_query):
    result = await check_contract_status(address_query=address_query)
    contract_id = result.get('id', 'unknown')
    status = result.get('status', 'unknown').replace('_', ' ')
    contract_name = result.get('name', 'contract')
    voice_response = f"Contract number {contract_id}, the {contract_name}, is {status}. "
    if 'submitters' in result and result['submitters']:
        submitters = result['submitters']
        total = len(submitters)
        completed = sum(1 for s in submitters if s.get('status') == 'completed')
        voice_response += f"{completed} of {total} signers have completed. "
        pending = [s['name'] for s in submitters if s.get('status') != 'completed']
        if pending:
            if len(pending) == 1:
                voice_response += f"Still waiting on {pending[0]}."
            else:
                voice_response += f"Still waiting on: {', '.join(pending[:-1])}, and {pending[-1]}."
        else:
            voice_response += "All signers have completed!"
    return {"voice_response": voice_response, "contract_id": contract_id, "status": status, "full_details": result}


async def check_property_contract_readiness(property_id=None, address_query=None):
    if address_query and not property_id:
        from app.database import SessionLocal
        from app.models.property import Property
        from sqlalchemy import func, or_
        db = SessionLocal()
        try:
            query_variations = normalize_voice_query(address_query)
            property_obj = db.query(Property).filter(or_(*[func.lower(Property.address).contains(var) for var in query_variations])).first()
            if not property_obj:
                raise ValueError(f"No property found matching: {address_query}")
            property_id = property_obj.id
        finally:
            db.close()
    if not property_id:
        raise ValueError("Either property_id or address_query must be provided")
    response = api_get(f"/contracts/property/{property_id}/required-status")
    response.raise_for_status()
    return response.json()


async def check_property_contract_readiness_voice(address_query):
    result = await check_property_contract_readiness(address_query=address_query)
    property_address = result.get('property_address', address_query)
    is_ready = result.get('is_ready_to_close', False)
    total = result.get('total_required', 0)
    completed = result.get('completed', 0)
    in_progress = result.get('in_progress', 0)
    missing = result.get('missing', 0)
    if is_ready:
        voice_response = f"Great news! {property_address} is ready to close. All {total} required contracts have been completed and signed."
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
        if missing > 0 and result.get('missing_templates'):
            voice_response += "Missing contracts: "
            missing_names = [t['name'] for t in result['missing_templates'][:3]]
            voice_response += ", ".join(missing_names)
            if len(result['missing_templates']) > 3:
                voice_response += f", and {len(result['missing_templates']) - 3} more"
            voice_response += "."
    return {"voice_response": voice_response, "is_ready_to_close": is_ready, "total_required": total, "completed": completed, "in_progress": in_progress, "missing": missing, "property_address": property_address, "full_details": result}


async def get_signing_status(property_id):
    response = api_get(f"/contracts/property/{property_id}/signing-status")
    response.raise_for_status()
    return response.json()


# ── Handlers ──

async def handle_send_contract(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    await send_contract(property_id=property_id, contact_id=arguments["contact_id"], contract_name=arguments.get("contract_name", "Purchase Agreement"), docuseal_template_id=arguments.get("docuseal_template_id"))
    return [TextContent(type="text", text=f"Contract '{arguments.get('contract_name', 'Purchase Agreement')}' sent for signing to contact {arguments['contact_id']} for property {property_id}.")]


async def handle_check_contract_status(arguments: dict) -> list[TextContent]:
    contract_id = arguments.get("contract_id")
    address_query = arguments.get("address_query")
    result = await check_contract_status(contract_id=contract_id, address_query=address_query)
    contract_id_display = result.get('id', contract_id or 'unknown')
    status_text = f"Contract #{contract_id_display}: {result.get('status', 'unknown')}."
    if "submitters" in result and result["submitters"]:
        signer_parts = [f"{s.get('name', 'Unknown')} ({s.get('role', '?')}): {s.get('status', 'pending')}" for s in result["submitters"]]
        status_text += f" Signers: {', '.join(signer_parts)}."
    return [TextContent(type="text", text=status_text)]


async def handle_list_contracts(arguments: dict) -> list[TextContent]:
    property_id = arguments.get("property_id")
    address_query = arguments.get("address_query")
    result = await list_contracts(property_id=property_id, address_query=address_query)
    if isinstance(result, list) and len(result) > 0:
        addr_label = f" for {address_query}" if address_query else ""
        summary = f"Found {len(result)} contract(s){addr_label}.\n\n"
        for contract in result:
            summary += f"#{contract['id']} {contract['name']} — {contract.get('status', 'unknown')}\n"
        return [TextContent(type="text", text=summary.strip())]
    else:
        return [TextContent(type="text", text=f"No contracts found{' for address: ' + address_query if address_query else ''}.")]


async def handle_list_contracts_voice(arguments: dict) -> list[TextContent]:
    address_query = arguments["address_query"]
    result = await list_contracts_voice(address_query=address_query)
    voice_text = result['voice_response']
    if result['contracts']:
        contract_parts = [f"{c['name']} ({c['status']})" for c in result['contracts']]
        voice_text += f" Contracts: {', '.join(contract_parts)}."
    return [TextContent(type="text", text=voice_text)]


async def handle_check_contract_status_voice(arguments: dict) -> list[TextContent]:
    address_query = arguments["address_query"]
    result = await check_contract_status_voice(address_query=address_query)
    return [TextContent(type="text", text=result['voice_response'])]


async def handle_get_signing_status(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    result = await get_signing_status(property_id=property_id)
    signing_text = result.get('voice_summary', f"Signing status for {result.get('property_address', 'Unknown')}: {result.get('signed', 0)}/{result.get('total_signers', 0)} signed.")
    for contract in result.get('contracts', []):
        signer_parts = [f"{s['name']} ({s['role']}): {s['status']}" for s in contract.get('signers', [])]
        signer_str = f" — {', '.join(signer_parts)}" if signer_parts else " — no signers assigned"
        signing_text += f"\n{contract['contract_name']} ({contract['contract_status']}){signer_str}."
    if result.get('pending_names'):
        signing_text += f"\nWaiting on: {', '.join(result['pending_names'])}."
    elif result.get('all_signed'):
        signing_text += "\nAll signers have completed!"
    return [TextContent(type="text", text=signing_text)]


async def handle_check_property_contract_readiness(arguments: dict) -> list[TextContent]:
    property_id = arguments.get("property_id")
    address_query = arguments.get("address_query")
    result = await check_property_contract_readiness(property_id=property_id, address_query=address_query)
    is_ready = result.get('is_ready_to_close', False)
    addr = result.get('property_address', 'Unknown')
    report = f"{addr}: {'ready to close' if is_ready else 'not ready to close'}. {result.get('completed', 0)}/{result.get('total_required', 0)} required contracts completed, {result.get('in_progress', 0)} in progress, {result.get('missing', 0)} missing."
    if result.get('missing_templates'):
        missing_names = [t['name'] for t in result['missing_templates']]
        report += f" Missing: {', '.join(missing_names)}."
    if result.get('incomplete_contracts'):
        in_progress_names = [f"{c['name']} ({c['status']})" for c in result['incomplete_contracts']]
        report += f" In progress: {', '.join(in_progress_names)}."
    return [TextContent(type="text", text=report)]


async def handle_check_property_contract_readiness_voice(arguments: dict) -> list[TextContent]:
    address_query = arguments["address_query"]
    result = await check_property_contract_readiness_voice(address_query=address_query)
    return [TextContent(type="text", text=result['voice_response'])]


# ── Tool Registration ──

register_tool(Tool(name="send_contract", description="Send a contract to a contact for signing via DocuSeal. Creates the contract and sends it to the specified contact. Voice-friendly: say the address instead of the ID.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID (optional if address provided)"}, "address": {"type": "string", "description": "Property address (voice-friendly)"}, "contact_id": {"type": "number", "description": "Contact ID (the person to sign)"}, "contract_name": {"type": "string", "description": "Name of the contract (default: Purchase Agreement)", "default": "Purchase Agreement"}, "docuseal_template_id": {"type": "string", "description": "DocuSeal template ID (optional)"}}, "required": ["contact_id"]}), handle_send_contract)

register_tool(Tool(name="check_contract_status", description="Check the status of a contract including signer details. Can look up by contract ID or property address. Voice-friendly: 'Check the contract status for 123 Main Street'.", inputSchema={"type": "object", "properties": {"contract_id": {"type": "number", "description": "Contract ID to check"}, "address_query": {"type": "string", "description": "Property address to find contracts for (voice-friendly)"}}}), handle_check_contract_status)

register_tool(Tool(name="list_contracts", description="List contracts, optionally filtered by property ID or address. Voice-friendly: 'List contracts for 123 Main Street'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Filter by property ID"}, "address_query": {"type": "string", "description": "Property address to search for (voice-friendly)"}}}), handle_list_contracts)

register_tool(Tool(name="list_contracts_voice", description="Voice-optimized contract listing with natural language response. Returns contract status breakdown in a format optimized for voice output. Voice: 'What contracts are there for 123 Main Street?'.", inputSchema={"type": "object", "properties": {"address_query": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street' or 'the Brooklyn property')"}}, "required": ["address_query"]}), handle_list_contracts_voice)

register_tool(Tool(name="check_contract_status_voice", description="Voice-optimized contract status check with natural language response. Returns signer status and pending items in voice-friendly format. Voice: 'What's the contract status for 123 Main Street?'.", inputSchema={"type": "object", "properties": {"address_query": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street')"}}, "required": ["address_query"]}), handle_check_contract_status_voice)

register_tool(Tool(name="get_signing_status", description="Get detailed signing status for all contracts on a property. Shows who has signed, who hasn't, and overall progress. Voice-friendly: say the address instead of the ID.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID (optional if address provided)"}, "address": {"type": "string", "description": "Property address (voice-friendly)"}}}), handle_get_signing_status)

register_tool(Tool(name="check_property_contract_readiness", description="Check if a property has all required contracts signed and is ready to close. Returns readiness status with breakdown of completed/in-progress/missing contracts. Voice-friendly: say the address.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID (optional if address provided)"}, "address_query": {"type": "string", "description": "Property address (voice-friendly)"}}}), handle_check_property_contract_readiness)

register_tool(Tool(name="check_property_contract_readiness_voice", description="Voice-optimized check if property is ready to close. Returns natural language response about contract completion status. Voice: 'Is 123 Main Street ready to close?'.", inputSchema={"type": "object", "properties": {"address_query": {"type": "string", "description": "Property address (voice-friendly, e.g., '123 Main Street')"}}, "required": ["address_query"]}), handle_check_property_contract_readiness_voice)
