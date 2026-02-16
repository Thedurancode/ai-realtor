"""Deal type and webhook MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post, api_put, api_delete
from ..utils.property_resolver import resolve_property_id


# ── Helpers ──

async def set_deal_type(property_id: int, deal_type_name: str, clear_previous: bool = False) -> dict:
    response = api_post(f"/properties/{property_id}/set-deal-type", params={"deal_type_name": deal_type_name, "clear_previous": clear_previous})
    response.raise_for_status()
    return response.json()


async def get_deal_status(property_id: int) -> dict:
    response = api_get(f"/properties/{property_id}/deal-status")
    response.raise_for_status()
    return response.json()


async def list_deal_types_api() -> list:
    response = api_get("/deal-types/")
    response.raise_for_status()
    return response.json()


async def get_deal_type_config(name: str) -> dict:
    response = api_get(f"/deal-types/{name}")
    response.raise_for_status()
    return response.json()


async def create_deal_type_config(data: dict) -> dict:
    response = api_post("/deal-types/", json=data)
    response.raise_for_status()
    return response.json()


async def update_deal_type_config(name: str, data: dict) -> dict:
    response = api_put(f"/deal-types/{name}", json=data)
    response.raise_for_status()
    return response.json()


async def delete_deal_type_config(name: str) -> dict:
    response = api_delete(f"/deal-types/{name}")
    if response.status_code == 204:
        return {"success": True, "name": name}
    response.raise_for_status()
    return response.json()


async def preview_deal_type_api(name: str, property_id: int) -> dict:
    response = api_post(f"/deal-types/{name}/preview", params={"property_id": property_id})
    response.raise_for_status()
    return response.json()


async def test_webhook_configuration() -> dict:
    response = api_get("/webhooks/docuseal/test")
    response.raise_for_status()
    return response.json()


# ── Handlers ──

async def handle_set_deal_type(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    deal_type_name = arguments["deal_type"]
    clear_previous = arguments.get("clear_previous", False)
    result = await set_deal_type(property_id=property_id, deal_type_name=deal_type_name, clear_previous=clear_previous)

    addr = result.get('property_address', 'the property')
    dt = result.get('deal_type', deal_type_name).replace('_', ' ').title()
    contracts_attached = result.get('contracts_attached', 0)
    todos_created = result.get('todos_created', 0)

    deal_text = f"Set {addr} as a {dt} deal."
    if result.get('contracts_removed', 0) > 0:
        deal_text += f" Removed {result['contracts_removed']} old contracts."
    if contracts_attached > 0:
        names = ', '.join(result.get('contract_names', []))
        deal_text += f" Attached {contracts_attached} contracts: {names}."
    if todos_created > 0:
        deal_text += f" Created {todos_created} checklist items."
    missing = result.get('missing_contacts', [])
    if missing:
        deal_text += f" Missing contacts: {', '.join(missing)} — add these to proceed."
    else:
        deal_text += " All required contacts are present."
    return [TextContent(type="text", text=deal_text)]


async def handle_get_deal_status(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    result = await get_deal_status(property_id=property_id)

    addr = result.get('property_address', 'This property')
    deal_type_display = result.get('deal_type')
    if not deal_type_display:
        return [TextContent(type="text", text=f"No deal type set for {addr}.")]

    contracts = result.get('contracts', {})
    checklist = result.get('checklist', {})
    contacts_info = result.get('contacts', {})
    missing = contacts_info.get('missing_roles', [])

    text = f"{addr} — {deal_type_display} deal."
    text += f" Contracts: {contracts.get('completed', 0)}/{contracts.get('total', 0)} done."
    pending = contracts.get('pending_names', [])
    if pending:
        text += f" Pending: {', '.join(pending)}."
    text += f" Checklist: {checklist.get('completed', 0)}/{checklist.get('total', 0)} done."
    if missing:
        text += f" Missing contacts: {', '.join(missing)}."
    if result.get('ready_to_close'):
        text += " READY TO CLOSE!"
    else:
        text += " Not ready to close yet."
    return [TextContent(type="text", text=text)]


async def handle_list_deal_types(arguments: dict) -> list[TextContent]:
    result = await list_deal_types_api()

    text = f"{len(result)} deal types available:\n\n"
    for dt in result:
        parts = []
        if dt.get('contract_templates'):
            parts.append(f"{len(dt['contract_templates'])} contracts")
        if dt.get('required_contact_roles'):
            parts.append(f"needs {', '.join(dt['required_contact_roles'])}")
        if dt.get('checklist'):
            parts.append(f"{len(dt['checklist'])} checklist items")
        detail = f" — {', '.join(parts)}" if parts else ""
        text += f"{dt['display_name']}{detail}\n"
    return [TextContent(type="text", text=text.strip())]


async def handle_get_deal_type_config(arguments: dict) -> list[TextContent]:
    dt_name = arguments["name"]
    result = await get_deal_type_config(dt_name)

    text = f"{result['display_name']}"
    if result.get('description'):
        text += f": {result['description']}"
    text += "."
    if result.get('contract_templates'):
        text += f"\nContracts: {', '.join(result['contract_templates'])}."
    if result.get('required_contact_roles'):
        text += f"\nRequired contacts: {', '.join(result['required_contact_roles'])}."
    if result.get('checklist'):
        items = [item['title'] for item in result['checklist']]
        text += f"\nChecklist ({len(items)} items): {', '.join(items)}."
    if result.get('compliance_tags'):
        text += f"\nCompliance: {', '.join(result['compliance_tags'])}."
    return [TextContent(type="text", text=text)]


async def handle_create_deal_type_config(arguments: dict) -> list[TextContent]:
    data = {"name": arguments["name"], "display_name": arguments["display_name"]}
    if arguments.get("description"):
        data["description"] = arguments["description"]
    if arguments.get("contract_templates"):
        data["contract_templates"] = arguments["contract_templates"]
    if arguments.get("required_contact_roles"):
        data["required_contact_roles"] = arguments["required_contact_roles"]
    if arguments.get("checklist"):
        data["checklist"] = arguments["checklist"]

    result = await create_deal_type_config(data)

    parts = []
    if result.get('contract_templates'):
        parts.append(f"{len(result['contract_templates'])} contracts")
    if result.get('required_contact_roles'):
        parts.append(f"needs {', '.join(result['required_contact_roles'])}")
    if result.get('checklist'):
        parts.append(f"{len(result['checklist'])} checklist items")
    detail = f" with {', '.join(parts)}" if parts else ""
    text = f"Deal type '{result['display_name']}' created{detail}. Use set_deal_type to apply it to a property."
    return [TextContent(type="text", text=text)]


async def handle_update_deal_type_config(arguments: dict) -> list[TextContent]:
    dt_name = arguments["name"]
    update_data = {k: v for k, v in arguments.items() if k != "name" and v is not None}
    result = await update_deal_type_config(dt_name, update_data)

    text = f"Deal type '{result['display_name']}' updated. Changes apply to future applications only — re-apply with set_deal_type and clear_previous=true to update existing properties."
    return [TextContent(type="text", text=text)]


async def handle_delete_deal_type_config(arguments: dict) -> list[TextContent]:
    dt_name = arguments["name"]
    await delete_deal_type_config(dt_name)
    return [TextContent(type="text", text=f"Deal type '{dt_name}' deleted successfully.")]


async def handle_preview_deal_type(arguments: dict) -> list[TextContent]:
    dt_name = arguments["name"]
    property_id = resolve_property_id(arguments)
    result = await preview_deal_type_api(dt_name, property_id)

    preview_text = f"PREVIEW: {result.get('deal_type', dt_name)} on Property {property_id}\n\n"
    preview_text += f"Property: {result.get('property_address', 'Unknown')}\n\n"
    would_create = result.get('would_create_contracts', [])
    would_skip = result.get('would_skip_contracts', [])
    if would_create:
        preview_text += f"Would CREATE {len(would_create)} contract(s):\n"
        for c in would_create:
            preview_text += f"  + {c}\n"
    if would_skip:
        preview_text += f"Would SKIP {len(would_skip)} (already exist):\n"
        for c in would_skip:
            preview_text += f"  - {c}\n"
    would_create_todos = result.get('would_create_todos', [])
    would_skip_todos = result.get('would_skip_todos', [])
    if would_create_todos:
        todo_names = [t.get('title', str(t)) for t in would_create_todos]
        preview_text += f" Would create {len(would_create_todos)} checklist items: {', '.join(todo_names)}."
    if would_skip_todos:
        preview_text += f" {len(would_skip_todos)} checklist items already exist."
    missing_roles = result.get('missing_contact_roles', [])
    present_roles = result.get('present_contact_roles', [])
    if missing_roles:
        preview_text += f" Missing contacts: {', '.join(missing_roles)}."
    if present_roles:
        preview_text += f" Present contacts: {', '.join(present_roles)}."
    preview_text += " This is a dry run — nothing was changed."
    return [TextContent(type="text", text=preview_text)]


async def handle_test_webhook_configuration(arguments: dict) -> list[TextContent]:
    result = await test_webhook_configuration()

    secret_ok = result['webhook_secret_configured']
    webhook_text = f"Webhook URL: {result['webhook_url']}. Secret: {'configured' if secret_ok else 'NOT configured'}."
    webhook_text += f" Supported events: {', '.join(result['supported_events'])}."
    steps = [f"{k}. {v}" for k, v in result['instructions'].items()]
    webhook_text += f" Setup: {' '.join(steps)}"
    if not secret_ok:
        webhook_text += " WARNING: Set DOCUSEAL_WEBHOOK_SECRET for security."
    return [TextContent(type="text", text=webhook_text)]


# ── Tool Registration ──

register_tool(Tool(name="set_deal_type", description="SET DEAL TYPE: Set a deal type on a property to trigger a full workflow. Voice-friendly: say the address instead of the ID. Example: 'Set 123 Main Street as a short sale' or 'Change the Brooklyn property to wholesale'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID (optional if address provided)"}, "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street')"}, "deal_type": {"type": "string", "description": "Deal type name: traditional, short_sale, reo, fsbo, new_construction, wholesale, rental, commercial (or custom)"}, "clear_previous": {"type": "boolean", "description": "If true and switching deal types, removes draft contracts and pending todos from the old deal type first. Completed/signed contracts are never removed. Default: false", "default": False}}, "required": ["deal_type"]}), handle_set_deal_type)

register_tool(Tool(name="get_deal_status", description="DEAL STATUS: Check the deal progress for a property. Voice-friendly: say the address instead of the ID. Example: 'What's the deal status for 123 Main Street?'", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID (optional if address provided)"}, "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street')"}}}), handle_get_deal_status)

register_tool(Tool(name="list_deal_types", description="LIST DEAL TYPES: Show all available deal types and what each one triggers (contracts, checklist, required contacts). Useful for 'What deal types are available?' or 'What does a short sale include?'", inputSchema={"type": "object", "properties": {}}), handle_list_deal_types)

register_tool(Tool(name="get_deal_type_config", description="GET DEAL TYPE CONFIG: Get full details of a specific deal type — its contracts, required contacts, checklist items, and compliance tags. Example: 'Show me the short sale config' or 'What contracts does a wholesale deal need?'", inputSchema={"type": "object", "properties": {"name": {"type": "string", "description": "Deal type name (e.g., 'short_sale', 'traditional', 'rental')"}}, "required": ["name"]}), handle_get_deal_type_config)

register_tool(Tool(name="create_deal_type_config", description="CREATE CUSTOM DEAL TYPE: Create a new deal type with custom contracts, required contacts, and checklist. Example: '1031 Exchange' with contracts like 'Exchange Agreement' and required roles like buyer + seller + intermediary.", inputSchema={"type": "object", "properties": {"name": {"type": "string", "description": "Unique identifier (lowercase, underscores, e.g., '1031_exchange')"}, "display_name": {"type": "string", "description": "Human-readable name (e.g., '1031 Exchange')"}, "description": {"type": "string", "description": "Description of this deal type"}, "contract_templates": {"type": "array", "items": {"type": "string"}, "description": "Contract names to auto-attach (e.g., ['Purchase Agreement', 'Exchange Agreement'])"}, "required_contact_roles": {"type": "array", "items": {"type": "string"}, "description": "Required contact roles (e.g., ['buyer', 'seller', 'lender'])"}, "checklist": {"type": "array", "items": {"type": "object", "properties": {"title": {"type": "string"}, "description": {"type": "string"}, "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]}, "due_days": {"type": "number"}}, "required": ["title"]}, "description": "Checklist items to auto-create as todos"}}, "required": ["name", "display_name"]}), handle_create_deal_type_config)

register_tool(Tool(name="update_deal_type_config", description="UPDATE DEAL TYPE CONFIG: Change the contracts, required contacts, checklist, or other settings on a deal type. Example: 'Add Bank Authorization to the short sale contracts' or 'Remove lender from traditional required contacts'. Changes apply to future deal type applications only.", inputSchema={"type": "object", "properties": {"name": {"type": "string", "description": "Deal type name to update (e.g., 'short_sale')"}, "display_name": {"type": "string", "description": "New display name"}, "description": {"type": "string", "description": "New description"}, "contract_templates": {"type": "array", "items": {"type": "string"}, "description": "Full list of contract names (replaces existing list)"}, "required_contact_roles": {"type": "array", "items": {"type": "string"}, "description": "Full list of required roles (replaces existing list)"}, "checklist": {"type": "array", "items": {"type": "object", "properties": {"title": {"type": "string"}, "description": {"type": "string"}, "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]}, "due_days": {"type": "number"}}, "required": ["title"]}, "description": "Full checklist (replaces existing list)"}, "is_active": {"type": "boolean", "description": "Enable or disable this deal type"}}, "required": ["name"]}), handle_update_deal_type_config)

register_tool(Tool(name="delete_deal_type_config", description="DELETE DEAL TYPE: Delete a custom deal type config. Cannot delete built-in deal types (traditional, short_sale, etc). Example: 'Delete the 1031 exchange deal type'.", inputSchema={"type": "object", "properties": {"name": {"type": "string", "description": "Deal type name to delete"}}, "required": ["name"]}), handle_delete_deal_type_config)

register_tool(Tool(name="preview_deal_type", description="PREVIEW DEAL TYPE: Dry run — see what would happen if you applied a deal type to a property. Voice-friendly: say the address. Example: 'Preview a short sale for 123 Main Street'.", inputSchema={"type": "object", "properties": {"name": {"type": "string", "description": "Deal type name to preview"}, "property_id": {"type": "number", "description": "Property ID (optional if address provided)"}, "address": {"type": "string", "description": "Property address to search for (voice-friendly, e.g., '123 Main Street')"}}, "required": ["name"]}), handle_preview_deal_type)

register_tool(Tool(name="test_webhook_configuration", description="TEST WEBHOOK SETUP: Check DocuSeal webhook configuration status and get setup instructions. Shows webhook URL, whether secret is configured, supported events, and step-by-step setup guide for connecting DocuSeal to automatically update contracts when signed.", inputSchema={"type": "object", "properties": {}}), handle_test_webhook_configuration)
