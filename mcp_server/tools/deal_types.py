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

    deal_text = f"DEAL TYPE SET\n\n"
    deal_text += f"Property: {result.get('property_address', 'Unknown')}\n"
    deal_text += f"Deal Type: {result.get('deal_type', deal_type_name)}\n\n"
    if result.get('contracts_removed', 0) > 0:
        deal_text += f"Removed {result['contracts_removed']} old contract(s): {', '.join(result.get('contracts_removed_names', []))}\n"
    if result.get('todos_removed', 0) > 0:
        deal_text += f"Removed {result['todos_removed']} old todo(s): {', '.join(result.get('todos_removed_titles', []))}\n"
    if result.get('contracts_removed', 0) > 0 or result.get('todos_removed', 0) > 0:
        deal_text += "\n"
    deal_text += f"Contracts Attached: {result.get('contracts_attached', 0)}\n"
    for name_c in result.get('contract_names', []):
        deal_text += f"  - {name_c}\n"
    deal_text += f"\nChecklist Items Created: {result.get('todos_created', 0)}\n"
    for title in result.get('todo_titles', []):
        deal_text += f"  - {title}\n"
    missing = result.get('missing_contacts', [])
    if missing:
        deal_text += f"\nMissing Required Contacts: {', '.join(missing)}\n"
        deal_text += "Add these contacts to proceed with the deal.\n"
    else:
        deal_text += f"\nAll required contacts are present.\n"
    return [TextContent(type="text", text=deal_text)]


async def handle_get_deal_status(arguments: dict) -> list[TextContent]:
    property_id = resolve_property_id(arguments)
    result = await get_deal_status(property_id=property_id)

    status_text = f"DEAL STATUS\n\n"
    status_text += f"Property: {result.get('property_address', 'Unknown')}\n"
    deal_type_display = result.get('deal_type')
    if not deal_type_display:
        status_text += "No deal type set for this property.\n"
        return [TextContent(type="text", text=status_text)]

    status_text += f"Deal Type: {deal_type_display}\n\n"
    contracts = result.get('contracts', {})
    status_text += f"CONTRACTS: {contracts.get('completed', 0)}/{contracts.get('total', 0)} completed\n"
    for n in contracts.get('pending_names', []):
        status_text += f"  Pending: {n}\n"
    for n in contracts.get('completed_names', []):
        status_text += f"  Done: {n}\n"
    checklist = result.get('checklist', {})
    status_text += f"\nCHECKLIST: {checklist.get('completed', 0)}/{checklist.get('total', 0)} completed\n"
    for item in checklist.get('pending_items', []):
        status_text += f"  Pending: {item['title']} ({item['priority']})\n"
    contacts_info = result.get('contacts', {})
    missing = contacts_info.get('missing_roles', [])
    if missing:
        status_text += f"\nMissing Contacts: {', '.join(missing)}\n"
    else:
        status_text += f"\nAll required contacts present\n"
    status_text += f"\n{'READY TO CLOSE!' if result.get('ready_to_close') else 'Not ready to close yet.'}\n"
    return [TextContent(type="text", text=status_text)]


async def handle_list_deal_types(arguments: dict) -> list[TextContent]:
    result = await list_deal_types_api()

    types_text = f"AVAILABLE DEAL TYPES ({len(result)})\n\n"
    for dt in result:
        types_text += f"{dt['display_name']} ({dt['name']})\n"
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
    return [TextContent(type="text", text=types_text)]


async def handle_get_deal_type_config(arguments: dict) -> list[TextContent]:
    dt_name = arguments["name"]
    result = await get_deal_type_config(dt_name)

    config_text = f"DEAL TYPE CONFIG: {result['display_name']}\n\n"
    if result.get('description'):
        config_text += f"{result['description']}\n\n"
    config_text += f"Name: {result['name']}\n"
    config_text += f"Built-in: {'Yes' if result.get('is_builtin') else 'No'}\n"
    config_text += f"Active: {'Yes' if result.get('is_active') else 'No'}\n\n"
    if result.get('contract_templates'):
        config_text += f"Contracts ({len(result['contract_templates'])}):\n"
        for ct in result['contract_templates']:
            config_text += f"  - {ct}\n"
    if result.get('required_contact_roles'):
        config_text += f"\nRequired Contacts: {', '.join(result['required_contact_roles'])}\n"
    if result.get('checklist'):
        config_text += f"\nChecklist ({len(result['checklist'])} items):\n"
        for item in result['checklist']:
            priority = item.get('priority', 'medium')
            config_text += f"  - {item['title']} ({priority})\n"
            if item.get('description'):
                config_text += f"    {item['description']}\n"
    if result.get('compliance_tags'):
        config_text += f"\nCompliance Tags: {', '.join(result['compliance_tags'])}\n"
    return [TextContent(type="text", text=config_text)]


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

    create_text = f"DEAL TYPE CREATED: {result['display_name']}\n\n"
    create_text += f"Name: {result['name']}\n"
    if result.get('contract_templates'):
        create_text += f"Contracts: {', '.join(result['contract_templates'])}\n"
    if result.get('required_contact_roles'):
        create_text += f"Required Contacts: {', '.join(result['required_contact_roles'])}\n"
    if result.get('checklist'):
        create_text += f"Checklist: {len(result['checklist'])} items\n"
    create_text += f"\nYou can now use 'set_deal_type' to apply it to a property.\n"
    return [TextContent(type="text", text=create_text)]


async def handle_update_deal_type_config(arguments: dict) -> list[TextContent]:
    dt_name = arguments["name"]
    update_data = {k: v for k, v in arguments.items() if k != "name" and v is not None}
    result = await update_deal_type_config(dt_name, update_data)

    update_text = f"DEAL TYPE UPDATED: {result['display_name']}\n\n"
    update_text += f"Name: {result['name']}\n"
    if result.get('contract_templates'):
        update_text += f"Contracts: {', '.join(result['contract_templates'])}\n"
    if result.get('required_contact_roles'):
        update_text += f"Required Contacts: {', '.join(result['required_contact_roles'])}\n"
    if result.get('checklist'):
        update_text += f"Checklist: {len(result['checklist'])} items\n"
    update_text += f"\nNote: Changes apply to future deal type applications only.\n"
    update_text += f"To update an existing property, re-apply with set_deal_type (clear_previous=true).\n"
    return [TextContent(type="text", text=update_text)]


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
        preview_text += f"\nWould CREATE {len(would_create_todos)} checklist item(s):\n"
        for t in would_create_todos:
            preview_text += f"  + {t.get('title', t)}\n"
    if would_skip_todos:
        preview_text += f"Would SKIP {len(would_skip_todos)} (already exist):\n"
        for t in would_skip_todos:
            preview_text += f"  - {t.get('title', t)}\n"
    missing_roles = result.get('missing_contact_roles', [])
    present_roles = result.get('present_contact_roles', [])
    if missing_roles:
        preview_text += f"\nMissing contacts: {', '.join(missing_roles)}\n"
    if present_roles:
        preview_text += f"Present contacts: {', '.join(present_roles)}\n"
    preview_text += f"\nThis is a dry run — nothing was changed.\n"
    return [TextContent(type="text", text=preview_text)]


async def handle_test_webhook_configuration(arguments: dict) -> list[TextContent]:
    result = await test_webhook_configuration()

    webhook_text = f"WEBHOOK CONFIGURATION STATUS\n\n"
    webhook_text += f"Webhook URL: {result['webhook_url']}\n"
    webhook_text += f"Secret Configured: {'YES' if result['webhook_secret_configured'] else 'NO'}\n\n"
    webhook_text += f"SUPPORTED EVENTS:\n"
    for event in result['supported_events']:
        webhook_text += f"  - {event}\n"
    webhook_text += f"\nSETUP INSTRUCTIONS:\n"
    for step_num, instruction in result['instructions'].items():
        webhook_text += f"  {step_num}. {instruction}\n"
    if not result['webhook_secret_configured']:
        webhook_text += f"\nWARNING: Webhook secret not configured! Set DOCUSEAL_WEBHOOK_SECRET environment variable for security.\n"
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
