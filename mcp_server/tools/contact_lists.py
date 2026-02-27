"""
Contact Lists MCP Tools - Voice Commands for Smart Contact Lists
"""
import httpx
from mcp.types import Tool, TextContent
from mcp_server.server import register_tool
from mcp_server.tools.base import API_BASE_URL, SessionLocal
from typing import Dict, Any, List
from sqlalchemy.orm import Session


# ==========================================================================
# GET CONTACT LISTS
# ==========================================================================

async def handle_list_contact_lists(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    List all contact lists

    Voice: "Show me all my contact lists"
    Voice: "What smart lists do I have?"
    """
    list_type = arguments.get("list_type")

    params = {}
    if list_type:
        params["list_type"] = list_type

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/contact-lists",
            params=params,
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()

    if not result:
        return [TextContent(
            type="text",
            text="You don't have any contact lists yet. Say 'create a smart list for contacts this week' to get started."
        )]

    # Build voice summary
    total_lists = len(result)
    smart_lists = [l for l in result if l["list_type"] == "smart"]
    manual_lists = [l for l in result if l["list_type"] == "manual"]

    voice_lines = [f"You have {total_lists} contact list{'s' if total_lists != 1 else ''}:"]

    for lst in result[:5]:  # Show first 5
        list_type = lst["list_type"]
        contacts = lst["total_contacts"]
        voice_lines.append(f"- {lst['name']} ({list_type}): {contacts} contacts")

    if len(result) > 5:
        voice_lines.append(f"... and {len(result) - 5} more")

    return [TextContent(
        type="text",
        text="\n".join(voice_lines)
    )]


async def handle_get_smart_list_presets(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Get available smart list presets

    Voice: "What smart list presets are available?"
    Voice: "Show me quick list options"
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/contact-lists/presets",
            timeout=30.0
        )
        response.raise_for_status()
        presets = response.json()

    voice_lines = ["Available smart list presets:"]
    for preset in presets:
        voice_lines.append(f"- {preset['display_name']}: {preset['description']}")

    voice_lines.append("\nVoice: 'Create {preset} list' to use one")

    return [TextContent(
        type="text",
        text="\n".join(voice_lines)
    )]


# ==========================================================================
# CREATE CONTACT LISTS
# ==========================================================================

async def handle_create_smart_list(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Create a smart list with auto-population

    Voice: "Create a smart list for contacts added this week"
    Voice: "Create a list for new leads in the last 2 days"
    Voice: "Make a list for uncontacted leads"
    """
    name = arguments.get("name")
    smart_rule = arguments.get("smart_rule")
    filters = arguments.get("filters")
    auto_refresh = arguments.get("auto_refresh", True)

    if not smart_rule:
        return [TextContent(
            type="text",
            text="Please specify a smart rule. Available: last_24_hours, last_2_days, last_7_days, this_week, this_month, no_property, has_property, no_phone, has_email"
        )]

    # Auto-generate name if not provided
    if not name:
        rule_names = {
            "last_24_hours": "New Contacts - Last 24 Hours",
            "last_2_days": "New Leads - Last 2 Days",
            "last_7_days": "New Leads - Last 7 Days",
            "this_week": "Interested This Week",
            "this_month": f"New Contacts - {__import__('datetime').datetime.now().strftime('%B %Y')}",
            "no_property": "No Property Linked",
            "has_property": "Has Property",
            "no_phone": "Missing Phone",
            "has_email": "Has Email",
            "uncontacted": "Uncontacted Leads"
        }
        name = rule_names.get(smart_rule, f"Smart List - {smart_rule}")

    payload = {
        "name": name,
        "smart_rule": smart_rule,
        "filters": filters,
        "auto_refresh": auto_refresh
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/contact-lists/smart",
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()

    return [TextContent(
        type="text",
        text=f"Smart list '{name}' created with {result['total_contacts']} contacts. "
             f"The list will auto-refresh daily to include new contacts matching the rule."
    )]


async def handle_create_quick_list(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Quick-create a smart list from preset

    Voice: "Create a list for contacts interested this week"
    Voice: "Make a new leads list for last 2 days"
    Voice: "Create uncontacted leads list"
    """
    preset = arguments.get("preset")
    custom_name = arguments.get("custom_name")
    filters = arguments.get("filters")

    # Map voice phrases to preset names
    preset_map = {
        "interested_this_week": "interested_this_week",
        "this_week": "interested_this_week",
        "new_leads_2days": "new_leads_2days",
        "last_2_days": "new_leads_2days",
        "new_leads_7days": "new_leads_7days",
        "last_7_days": "new_leads_7days",
        "this_month": "this_month",
        "uncontacted": "uncontacted",
        "no_phone": "no_phone",
        "has_email": "has_email",
        "no_property": "no_property"
    }

    # If preset not in map, try to find it
    if preset not in preset_map:
        # Check if it matches any key
        preset = preset_map.get(preset, preset)

    payload = {
        "preset": preset
    }
    if custom_name:
        payload["custom_name"] = custom_name
    if filters:
        payload["filters"] = filters

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/contact-lists/quick",
            json=payload,
            timeout=30.0
        )
        if response.status_code == 400:
            return [TextContent(
                type="text",
                text=f"Invalid preset. Available: interested_this_week, new_leads_2days, new_leads_7days, this_month, uncontacted, no_phone, has_email, no_property"
            )]
        response.raise_for_status()
        result = response.json()

    return [TextContent(
        type="text",
        text=f"Created '{result['name']}' with {result['total_contacts']} contacts. "
             f"List will auto-refresh daily."
    )]


async def handle_add_contacts_to_list(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Add contacts to a manual list

    Voice: "Add contacts 1, 2, and 3 to list 5"
    Voice: "Add these contacts to my follow-up list"
    """
    list_id = arguments.get("list_id")
    contact_ids = arguments.get("contact_ids", [])

    if not list_id:
        return [TextContent(
            type="text",
            text="Please provide a list_id"
        )]

    if not contact_ids:
        return [TextContent(
            type="text",
            text="Please provide contact_ids to add"
        )]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/contact-lists/{list_id}/contacts",
            json=contact_ids,
            timeout=30.0
        )
        if response.status_code == 400:
            return [TextContent(
                type="text",
                text="Can only add contacts to manual lists, not smart lists"
            )]
        response.raise_for_status()
        result = response.json()

    return [TextContent(
        type="text",
        text=f"Added {len(contact_ids)} contact{'s' if len(contact_ids) != 1 else ''} to list '{result['name']}'. "
             f"List now has {result['total_contacts']} contacts."
    )]


# ==========================================================================
# GET LIST DETAILS
# ==========================================================================

async def handle_get_contact_list(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Get contact list details with contacts

    Voice: "Show me list 5"
    Voice: "What's in my interested this week list?"
    Voice: "Get details for list 3"
    """
    list_id = arguments.get("list_id")
    include_contacts = arguments.get("include_contacts", True)
    limit = arguments.get("limit", 20)

    if not list_id:
        return [TextContent(
            type="text",
            text="Please provide a list_id"
        )]

    params = {
        "include_contacts": include_contacts,
        "limit": limit
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/contact-lists/{list_id}",
            params=params,
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()

    # Build voice summary
    list_type = result["list_type"]
    contacts = result.get("contacts", [])
    total = result["total_contacts"]

    voice_lines = [
        f"List: {result['name']}",
        f"Type: {list_type}",
        f"Total contacts: {total}"
    ]

    if list_type == "smart" and result.get("smart_rule"):
        voice_lines.append(f"Rule: {result['smart_rule']}")

    if contacts:
        voice_lines.append(f"\nShowing {len(contacts)} contacts:")
        for contact in contacts[:10]:  # Show first 10
            voice_lines.append(f"- {contact['name']}: {contact['address']}")
            if contact.get("phone"):
                voice_lines.append(f"  Phone: {contact['phone']}")
            if contact.get("email"):
                voice_lines.append(f"  Email: {contact['email']}")

        if len(contacts) > 10:
            voice_lines.append(f"... and {total - 10} more")

    return [TextContent(
        type="text",
        text="\n".join(voice_lines)
    )]


# ==========================================================================
# REFRESH AND DELETE
# ==========================================================================

async def handle_refresh_smart_list(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Refresh a smart list to update contacts

    Voice: "Refresh smart list 5"
    Voice: "Update my interested this week list"
    """
    list_id = arguments.get("list_id")

    if not list_id:
        return [TextContent(
            type="text",
            text="Please provide a list_id"
        )]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/contact-lists/{list_id}/refresh",
            timeout=30.0
        )
        if response.status_code == 400:
            return [TextContent(
                type="text",
                text="Can only refresh smart lists"
            )]
        response.raise_for_status()
        result = response.json()

    return [TextContent(
        type="text",
        text=f"Refreshed '{result['name']}'. Now has {result['total_contacts']} contacts. "
             f"Last refreshed: {result.get('last_refreshed_at', 'now')}"
    )]


async def handle_delete_contact_list(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Delete a contact list

    Voice: "Delete list 5"
    Voice: "Remove my old list"
    """
    list_id = arguments.get("list_id")

    if not list_id:
        return [TextContent(
            type="text",
            text="Please provide a list_id"
        )]

    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{API_BASE_URL}/contact-lists/{list_id}",
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()

    return [TextContent(
        type="text",
        text=result["message"]
    )]


# ==========================================================================
# CAMPAIGN FROM LIST
# ==========================================================================

async def handle_create_campaign_from_list(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Create a direct mail campaign from a contact list

    Voice: "Create a campaign from list 5"
    Voice: "Send postcards to my interested this week list"
    Voice: "Create campaign for list 3 using interested in selling template"
    """
    list_id = arguments.get("list_id")
    template = arguments.get("template", "interested_in_selling")
    campaign_name = arguments.get("campaign_name")
    send_immediately = arguments.get("send_immediately", False)

    if not list_id:
        return [TextContent(
            type="text",
            text="Please provide a list_id"
        )]

    params = {
        "template": template,
        "send_immediately": send_immediately
    }
    if campaign_name:
        params["campaign_name"] = campaign_name

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/contact-lists/{list_id}/create-campaign",
            params=params,
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()

    return [TextContent(
        type="text",
        text=f"Campaign '{result['campaign_name']}' created from list with {result['contact_count']} contacts. "
             f"Campaign ID: {result['campaign_id']}. "
             f"{'Sending immediately!' if send_immediately else 'Scheduled for later.'}"
    )]


# ==========================================================================
# REGISTER TOOLS
# ==========================================================================

register_tool(
    Tool(
        name="list_contact_lists",
        description="List all contact lists. Voice: 'Show me all my contact lists' or 'What smart lists do I have?'.",
        inputSchema={
            "type": "object",
            "properties": {
                "list_type": {"type": "string", "description": "Filter by type (smart, manual, imported, campaign)"}
            }
        }
    ),
    handle_list_contact_lists
)

register_tool(
    Tool(
        name="get_smart_list_presets",
        description="Get available smart list presets for quick creation. Voice: 'What smart list presets are available?' or 'Show me quick list options'.",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    handle_get_smart_list_presets
)

register_tool(
    Tool(
        name="create_smart_list",
        description="Create a smart list with auto-population. Voice: 'Create a smart list for contacts added this week' or 'Make a list for new leads in the last 2 days'.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "List name (auto-generates if omitted)"},
                "smart_rule": {"type": "string", "description": "Rule: last_24_hours, last_2_days, last_7_days, this_week, this_month, no_property, has_property, no_phone, has_email, uncontacted"},
                "filters": {"type": "object", "description": "Additional filters (city, state, etc.)"},
                "auto_refresh": {"type": "boolean", "description": "Auto-refresh daily", "default": true}
            }
        }
    ),
    handle_create_smart_list
)

register_tool(
    Tool(
        name="create_quick_list",
        description="Quick-create a smart list from preset. Voice: 'Create a list for contacts interested this week' or 'Make a new leads list for last 2 days'.",
        inputSchema={
            "type": "object",
            "properties": {
                "preset": {"type": "string", "description": "Preset: interested_this_week, new_leads_2days, new_leads_7days, this_month, uncontacted, no_phone, has_email, no_property"},
                "custom_name": {"type": "string", "description": "Custom name (optional)"},
                "filters": {"type": "object", "description": "Additional filters (city, state, etc.)"}
            }
        }
    ),
    handle_create_quick_list
)

register_tool(
    Tool(
        name="get_contact_list",
        description="Get contact list details with contacts. Voice: 'Show me list 5' or 'What's in my interested this week list?'.",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "number", "description": "List ID"},
                "include_contacts": {"type": "boolean", "description": "Include contacts in response", "default": true},
                "limit": {"type": "number", "description": "Max contacts to return", "default": 20}
            },
            "required": ["list_id"]
        }
    ),
    handle_get_contact_list
)

register_tool(
    Tool(
        name="add_contacts_to_list",
        description="Add contacts to a manual list. Voice: 'Add contacts 1, 2, and 3 to list 5' or 'Add these contacts to my follow-up list'.",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "number", "description": "List ID"},
                "contact_ids": {"type": "array", "items": {"type": "number"}, "description": "Contact IDs to add"}
            },
            "required": ["list_id", "contact_ids"]
        }
    ),
    handle_add_contacts_to_list
)

register_tool(
    Tool(
        name="refresh_smart_list",
        description="Refresh a smart list to update contacts. Voice: 'Refresh smart list 5' or 'Update my interested this week list'.",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "number", "description": "List ID"}
            },
            "required": ["list_id"]
        }
    ),
    handle_refresh_smart_list
)

register_tool(
    Tool(
        name="delete_contact_list",
        description="Delete a contact list. Voice: 'Delete list 5' or 'Remove my old list'.",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "number", "description": "List ID"}
            },
            "required": ["list_id"]
        }
    ),
    handle_delete_contact_list
)

register_tool(
    Tool(
        name="create_campaign_from_list",
        description="Create a direct mail campaign from a contact list. Voice: 'Create a campaign from list 5' or 'Send postcards to my interested this week list'.",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "number", "description": "List ID"},
                "template": {"type": "string", "description": "Template to use", "default": "interested_in_selling"},
                "campaign_name": {"type": "string", "description": "Custom campaign name"},
                "send_immediately": {"type": "boolean", "description": "Send immediately", "default": false}
            },
            "required": ["list_id"]
        }
    ),
    handle_create_campaign_from_list
)
