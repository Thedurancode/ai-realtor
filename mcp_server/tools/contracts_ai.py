"""AI-powered contract management MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_post, api_patch
from ..utils.voice import normalize_voice_query


# ── Helpers ──

def _resolve_property_from_address(address_query):
    from app.database import SessionLocal
    from app.models.property import Property
    from sqlalchemy import func, or_
    db = SessionLocal()
    try:
        query_variations = normalize_voice_query(address_query)
        property_obj = db.query(Property).filter(or_(*[func.lower(Property.address).contains(var) for var in query_variations])).first()
        if not property_obj:
            raise ValueError(f"No property found matching: {address_query}")
        return property_obj.id
    finally:
        db.close()


async def attach_required_contracts(property_id=None, address_query=None):
    if address_query and not property_id:
        property_id = _resolve_property_from_address(address_query)
    if not property_id:
        raise ValueError("Either property_id or address_query must be provided")
    response = api_post(f"/contracts/property/{property_id}/auto-attach")
    response.raise_for_status()
    return response.json()


async def ai_suggest_contracts_for_property(property_id=None, address_query=None):
    if address_query and not property_id:
        property_id = _resolve_property_from_address(address_query)
    if not property_id:
        raise ValueError("Either property_id or address_query must be provided")
    response = api_post(f"/contracts/property/{property_id}/ai-suggest")
    response.raise_for_status()
    return response.json()


async def apply_ai_contract_suggestions(property_id=None, address_query=None, only_required=True):
    if address_query and not property_id:
        property_id = _resolve_property_from_address(address_query)
    if not property_id:
        raise ValueError("Either property_id or address_query must be provided")
    response = api_post(f"/contracts/property/{property_id}/ai-apply-suggestions", params={"only_required": only_required})
    response.raise_for_status()
    return response.json()


async def mark_contract_required(contract_id, is_required=True, reason=None, required_by_date=None):
    response = api_patch(f"/contracts/{contract_id}/mark-required", params={"is_required": is_required, "reason": reason, "required_by_date": required_by_date})
    response.raise_for_status()
    return response.json()


async def smart_send_contract(address_query, contract_name, order="preserved", message=None, create_if_missing=True):
    response = api_post("/contracts/voice/smart-send", json={"address_query": address_query, "contract_name": contract_name, "order": order, "message": message, "create_if_missing": create_if_missing})
    response.raise_for_status()
    return response.json()


# ── Handlers ──

async def handle_attach_required_contracts(arguments: dict) -> list[TextContent]:
    result = await attach_required_contracts(property_id=arguments.get("property_id"), address_query=arguments.get("address_query"))
    attached_count = result.get('contracts_attached', 0)
    addr = result.get('property_address', 'the property')
    if attached_count > 0:
        names = [c['name'] for c in result.get('contracts', [])]
        text = f"Attached {attached_count} contract{'s' if attached_count != 1 else ''} to {addr}: {', '.join(names)}."
    else:
        text = f"No new contracts needed for {addr} — all applicable contracts already exist."
    return [TextContent(type="text", text=text)]


async def handle_ai_suggest_contracts(arguments: dict) -> list[TextContent]:
    result = await ai_suggest_contracts_for_property(property_id=arguments.get("property_id"), address_query=arguments.get("address_query"))
    addr = result.get('property_address', 'the property')
    total = result.get('total_suggested', 0)
    required = result.get('required_contracts', [])
    optional = result.get('optional_contracts', [])

    text = f"AI suggests {total} contract{'s' if total != 1 else ''} for {addr}."
    if required:
        req_parts = [f"{c['name']} ({c.get('reason', '')})" for c in required]
        text += f"\n\nRequired ({len(required)}): {'; '.join(req_parts)}."
    if optional:
        opt_names = [c['name'] for c in optional]
        text += f"\nOptional ({len(optional)}): {', '.join(opt_names)}."
    if result.get('summary'):
        text += f"\n\n{result['summary']}"
    return [TextContent(type="text", text=text.strip())]


async def handle_apply_ai_contract_suggestions(arguments: dict) -> list[TextContent]:
    only_required = arguments.get("only_required", True)
    result = await apply_ai_contract_suggestions(property_id=arguments.get("property_id"), address_query=arguments.get("address_query"), only_required=only_required)
    created_count = result.get('contracts_created', 0)
    addr = result.get('property_address', 'the property')
    mode = "required only" if only_required else "required + optional"
    if created_count > 0:
        names = [c['name'] for c in result.get('contracts', [])]
        text = f"Applied AI suggestions for {addr}: created {created_count} contract{'s' if created_count != 1 else ''} ({mode}) — {', '.join(names)}."
    else:
        text = f"No new contracts needed for {addr} — all AI-suggested contracts already exist."
    return [TextContent(type="text", text=text)]


async def handle_mark_contract_required(arguments: dict) -> list[TextContent]:
    contract_id = arguments["contract_id"]
    is_required = arguments.get("is_required", True)
    reason = arguments.get("reason")
    required_by_date = arguments.get("required_by_date")
    result = await mark_contract_required(contract_id=contract_id, is_required=is_required, reason=reason, required_by_date=required_by_date)
    status_word = "required" if is_required else "optional"
    name = result.get('contract_name', 'Unknown')
    text = f"Contract #{contract_id} ({name}) marked as {status_word}."
    if reason:
        text += f" Reason: {reason}."
    if required_by_date:
        text += f" Due by {required_by_date}."
    return [TextContent(type="text", text=text)]


async def handle_smart_send_contract(arguments: dict) -> list[TextContent]:
    result = await smart_send_contract(address_query=arguments["address_query"], contract_name=arguments["contract_name"], order=arguments.get("order", "preserved"), message=arguments.get("message"), create_if_missing=arguments.get("create_if_missing", True))
    text = result.get('voice_confirmation', f"{result['contract_name']} sent for {result['property_address']}.")
    if result.get('submitters'):
        signer_parts = [f"{s['name']} ({s['role']})" for s in result['submitters']]
        text += f" Sent to: {', '.join(signer_parts)}."
    if result.get('missing_roles'):
        text += f" Missing signers: {', '.join(result['missing_roles'])}."
    return [TextContent(type="text", text=text)]


# ── Tool Registration ──

register_tool(Tool(name="attach_required_contracts", description="Manually trigger auto-attach of required contracts to a property based on matching templates. Useful if property was created before templates were configured. Voice-friendly: say the address.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID (optional if address provided)"}, "address_query": {"type": "string", "description": "Property address (voice-friendly)"}}}), handle_attach_required_contracts)

register_tool(Tool(name="ai_suggest_contracts", description="AI-POWERED: Use Claude AI to analyze a property and suggest which contracts are required vs optional. Returns AI-powered recommendations based on property characteristics, state regulations, and industry best practices.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID (optional if address provided)"}, "address_query": {"type": "string", "description": "Property address (voice-friendly)"}}}), handle_ai_suggest_contracts)

register_tool(Tool(name="apply_ai_contract_suggestions", description="Apply AI contract suggestions by creating the recommended contracts for a property. By default only creates required contracts. Set only_required=false to include optional ones too.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID (optional if address provided)"}, "address_query": {"type": "string", "description": "Property address (voice-friendly)"}, "only_required": {"type": "boolean", "description": "Only create required contracts (default: true)", "default": True}}}), handle_apply_ai_contract_suggestions)

register_tool(Tool(name="mark_contract_required", description="Manually mark a contract as required or optional. This overrides AI suggestions and template defaults. Example: 'Mark contract 10 as required because the lender needs it'.", inputSchema={"type": "object", "properties": {"contract_id": {"type": "number", "description": "Contract ID to mark"}, "is_required": {"type": "boolean", "description": "True for required, false for optional", "default": True}, "reason": {"type": "string", "description": "Reason for override"}, "required_by_date": {"type": "string", "description": "Deadline date (YYYY-MM-DD)"}}, "required": ["contract_id"]}), handle_mark_contract_required)

register_tool(Tool(name="smart_send_contract", description="SMART SEND: Send a contract and automatically determine who needs to sign it. No need to specify contact roles! The system knows that a Purchase Agreement needs buyer + seller, an Inspection Report needs the inspector, etc. Just say the contract name and address. Example: 'Send the purchase agreement for 123 Main St' - system auto-finds buyer and seller contacts and sends to both.", inputSchema={"type": "object", "properties": {"address_query": {"type": "string", "description": "Natural language address (voice-friendly). Examples: 'one forty one throop', '123 main street'. Handles phonetic variations."}, "contract_name": {"type": "string", "description": "Name of the contract to send. Examples: 'Purchase Agreement', 'Inspection Report', 'Disclosure Form'. Fuzzy-matched to templates."}, "order": {"type": "string", "description": "Signing order: 'preserved' for sequential or 'random' for parallel. Default: preserved", "enum": ["preserved", "random"], "default": "preserved"}, "message": {"type": "string", "description": "Optional custom message to include in the signing email"}, "create_if_missing": {"type": "boolean", "description": "If true, auto-create the contract if it doesn't exist yet. Default: true", "default": True}}, "required": ["address_query", "contract_name"]}), handle_smart_send_contract)
