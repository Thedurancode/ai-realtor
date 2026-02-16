"""Voice campaign MCP tools for managing automated calling campaigns."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


# ── Handlers ──

async def handle_create_voice_campaign(arguments: dict) -> list[TextContent]:
    payload = {
        "name": arguments["name"],
        "call_purpose": arguments["call_purpose"],
        "description": arguments.get("description", ""),
        "property_id": arguments.get("property_id"),
        "contact_roles": arguments.get("contact_roles", []),
        "max_attempts": arguments.get("max_attempts", 3),
        "retry_delay_minutes": 60,
        "rate_limit_per_minute": 5,
        "auto_enroll_from_filters": arguments.get("auto_enroll", False),
    }
    response = api_post("/voice-campaigns/", json=payload)
    response.raise_for_status()
    campaign = response.json()

    text = f"Campaign '{campaign['name']}' created (ID: {campaign['id']})\n"
    text += f"Purpose: {campaign['call_purpose']} | Status: {campaign['status']}\n"
    if campaign.get("property_id"):
        text += f"Property: #{campaign['property_id']}\n"
    text += "\nUse start_voice_campaign to begin calling."
    return [TextContent(type="text", text=text)]


async def handle_add_campaign_targets(arguments: dict) -> list[TextContent]:
    campaign_id = arguments["campaign_id"]

    if arguments.get("contact_ids") or arguments.get("phone_numbers"):
        payload = {
            "contact_ids": arguments.get("contact_ids", []),
            "phone_numbers": arguments.get("phone_numbers", []),
            "property_id": arguments.get("property_id"),
        }
        response = api_post(f"/voice-campaigns/{campaign_id}/targets", json=payload)
    else:
        payload = {
            "property_id": arguments.get("property_id"),
            "contact_roles": arguments.get("contact_roles", []),
            "limit": arguments.get("limit", 100),
        }
        response = api_post(f"/voice-campaigns/{campaign_id}/targets/from-filters", json=payload)

    response.raise_for_status()
    result = response.json()

    added = result.get("added", 0)
    skipped = result.get("skipped", 0)
    text = f"Campaign #{campaign_id}: added {added} target(s)"
    if skipped:
        text += f", skipped {skipped} (already enrolled)"
    return [TextContent(type="text", text=text)]


async def handle_start_voice_campaign(arguments: dict) -> list[TextContent]:
    campaign_id = arguments["campaign_id"]
    response = api_post(f"/voice-campaigns/{campaign_id}/start")
    response.raise_for_status()
    campaign = response.json()
    return [TextContent(type="text", text=f"Campaign '{campaign['name']}' started. Status: {campaign['status']}")]


async def handle_pause_voice_campaign(arguments: dict) -> list[TextContent]:
    campaign_id = arguments["campaign_id"]
    response = api_post(f"/voice-campaigns/{campaign_id}/pause")
    response.raise_for_status()
    campaign = response.json()
    return [TextContent(type="text", text=f"Campaign '{campaign['name']}' paused.")]


async def handle_get_campaign_status(arguments: dict) -> list[TextContent]:
    campaign_id = arguments["campaign_id"]
    response = api_get(f"/voice-campaigns/{campaign_id}/analytics")
    response.raise_for_status()
    stats = response.json()

    total = stats.get("total_targets", 0)
    completed = stats.get("completed", 0)
    pending = stats.get("pending", 0)
    in_progress = stats.get("in_progress", 0)
    failed = stats.get("failed", 0)
    exhausted = stats.get("exhausted", 0)
    success_rate = stats.get("success_rate", 0)

    text = f"Campaign #{campaign_id}: {completed}/{total} completed ({success_rate:.0%} success rate). Pending: {pending}, in progress: {in_progress}, failed: {failed}, exhausted: {exhausted}."
    if stats.get("avg_attempts"):
        text += f" Average {stats['avg_attempts']:.1f} attempts per target."
    return [TextContent(type="text", text=text)]


async def handle_list_voice_campaigns(arguments: dict) -> list[TextContent]:
    params = {"limit": arguments.get("limit", 20)}
    if arguments.get("status"):
        params["status"] = arguments["status"]

    response = api_get("/voice-campaigns/", params=params)
    response.raise_for_status()
    campaigns = response.json()

    if not campaigns:
        return [TextContent(type="text", text="No campaigns found.")]

    text = f"You have {len(campaigns)} campaign(s).\n\n"
    for c in campaigns:
        line = f"#{c['id']} {c['name']} [{c['status']}] — {c['call_purpose']}"
        if c.get("property_id"):
            line += f", property #{c['property_id']}"
        text += line + "\n"
    return [TextContent(type="text", text=text.strip())]


# ── Tool Registration ──

register_tool(
    Tool(
        name="create_voice_campaign",
        description="Create a voice calling campaign to automatically reach out to contacts. "
                    "Campaigns can target contacts by role (buyer, seller, etc.) and property. "
                    "Voice: 'Create a campaign to call all sellers in Brooklyn'",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Campaign name (e.g., 'Brooklyn Sellers Outreach')"},
                "call_purpose": {
                    "type": "string",
                    "description": "Purpose of the calls",
                    "enum": ["property_update", "contract_reminder", "closing_ready",
                             "specific_contract_reminder", "skip_trace_outreach"],
                },
                "description": {"type": "string", "description": "Optional campaign description"},
                "property_id": {"type": "integer", "description": "Associate campaign with a property"},
                "contact_roles": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Filter contacts by role: buyer, seller, landlord, tenant, etc.",
                },
                "max_attempts": {"type": "integer", "default": 3, "description": "Max call attempts per target"},
                "auto_enroll": {"type": "boolean", "default": False, "description": "Auto-enroll matching contacts"},
            },
            "required": ["name", "call_purpose"],
        },
    ),
    handle_create_voice_campaign,
)

register_tool(
    Tool(
        name="add_campaign_targets",
        description="Add targets to a voice campaign. Provide contact IDs, phone numbers, "
                    "or use filters (property_id + contact_roles) to auto-enroll. "
                    "Voice: 'Add all contacts from property 5 to campaign 3'",
        inputSchema={
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer", "description": "Campaign ID"},
                "contact_ids": {"type": "array", "items": {"type": "integer"}, "description": "Specific contact IDs"},
                "phone_numbers": {"type": "array", "items": {"type": "string"}, "description": "Phone numbers in E.164 format"},
                "property_id": {"type": "integer", "description": "Property ID to filter contacts from"},
                "contact_roles": {"type": "array", "items": {"type": "string"}, "description": "Roles to filter: buyer, seller, etc."},
                "limit": {"type": "integer", "default": 100, "description": "Max targets to enroll from filters"},
            },
            "required": ["campaign_id"],
        },
    ),
    handle_add_campaign_targets,
)

register_tool(
    Tool(
        name="start_voice_campaign",
        description="Start a voice campaign to begin making calls. Campaign must have targets enrolled. "
                    "Voice: 'Start campaign 3'",
        inputSchema={
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer", "description": "Campaign ID to start"},
            },
            "required": ["campaign_id"],
        },
    ),
    handle_start_voice_campaign,
)

register_tool(
    Tool(
        name="pause_voice_campaign",
        description="Pause an active voice campaign. Can be resumed later. "
                    "Voice: 'Pause campaign 3'",
        inputSchema={
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer", "description": "Campaign ID to pause"},
            },
            "required": ["campaign_id"],
        },
    ),
    handle_pause_voice_campaign,
)

register_tool(
    Tool(
        name="get_campaign_status",
        description="Get analytics and status for a voice campaign. Shows completion rate, "
                    "targets reached, success rate, and more. "
                    "Voice: 'How is campaign 3 doing?'",
        inputSchema={
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer", "description": "Campaign ID"},
            },
            "required": ["campaign_id"],
        },
    ),
    handle_get_campaign_status,
)

register_tool(
    Tool(
        name="list_voice_campaigns",
        description="List voice campaigns with optional status filter. "
                    "Voice: 'Show me all active campaigns'",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter by status: draft, active, paused, completed, cancelled"},
                "limit": {"type": "integer", "default": 20, "description": "Max results"},
            },
        },
    ),
    handle_list_voice_campaigns,
)
