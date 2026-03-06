"""Follow-Up Sequence MCP tools — create and manage auto-drip campaigns."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_create_sequence(arguments: dict) -> list[TextContent]:
    lead_name = arguments.get("lead_name")
    if not lead_name:
        return [TextContent(type="text", text="Please provide the lead's name.")]

    payload = {"lead_name": lead_name}
    if arguments.get("lead_email"):
        payload["lead_email"] = arguments["lead_email"]
    if arguments.get("lead_phone"):
        payload["lead_phone"] = arguments["lead_phone"]
    if arguments.get("lead_source"):
        payload["lead_source"] = arguments["lead_source"]
    if arguments.get("template"):
        payload["template_name"] = arguments["template"]
    if arguments.get("temperature"):
        payload["temperature"] = arguments["temperature"]
    if arguments.get("property_id"):
        payload["property_id"] = arguments["property_id"]
    if arguments.get("context"):
        payload["custom_context"] = arguments["context"]

    response = api_post("/sequences/create", json=payload)
    response.raise_for_status()
    data = response.json()
    return [TextContent(type="text", text=f"Created follow-up sequence for {lead_name} — {data['steps']} touches. ID: {data['id']}")]


async def handle_list_sequences(arguments: dict) -> list[TextContent]:
    params = {}
    if arguments.get("status"):
        params["status"] = arguments["status"]

    response = api_get("/sequences/list", params=params)
    response.raise_for_status()
    data = response.json()

    if not data:
        return [TextContent(type="text", text="No follow-up sequences found.")]

    text = f"Follow-Up Sequences ({len(data)}):\n\n"
    for s in data:
        emoji = {"active": "ACTIVE", "paused": "PAUSED", "completed": "DONE", "cancelled": "CANCELLED"}.get(s["status"], s["status"])
        text += f"  #{s['id']} [{emoji}] {s['lead_name']} — {s['template']} | {s['progress']} steps"
        text += f" | Engagement: {s['engagement_score']:.0f}/100"
        if s.get("next_touch_at"):
            text += f" | Next: {s['next_touch_at'][:10]}"
        text += "\n"
        stats = s.get("stats", {})
        sent = stats.get("emails_sent", 0) + stats.get("sms_sent", 0) + stats.get("calls_made", 0) + stats.get("postcards_sent", 0)
        if sent > 0:
            text += f"     Sent: {sent} | Replies: {stats.get('replies', 0)}\n"

    return [TextContent(type="text", text=text)]


async def handle_get_sequence(arguments: dict) -> list[TextContent]:
    seq_id = arguments.get("sequence_id")
    if not seq_id:
        return [TextContent(type="text", text="Please provide a sequence_id.")]

    response = api_get(f"/sequences/{seq_id}")
    response.raise_for_status()
    data = response.json()

    text = f"Sequence #{data['id']}: {data['lead_name']}\n"
    text += f"Status: {data['status']} | Template: {data['template']}\n"
    text += f"Temperature: {data.get('temperature', '?')} | Engagement: {data['engagement_score']:.0f}/100\n"
    text += f"Progress: {data['progress']}\n\n"

    touches = data.get("touches", [])
    if touches:
        text += "Touches:\n"
        for t in touches:
            status_icon = {"sent": "SENT", "scheduled": "SCHEDULED", "opened": "OPENED", "replied": "REPLIED", "failed": "FAILED", "skipped": "SKIP"}.get(t["status"], t["status"])
            text += f"  Step {t['step']}: [{status_icon}] {t['channel']} (day {t['day']})"
            if t.get("sent_at"):
                text += f" — sent {t['sent_at'][:10]}"
            text += "\n"
            if t.get("message_preview"):
                text += f"    {t['message_preview']}\n"

    return [TextContent(type="text", text=text)]


async def handle_process_sequences(arguments: dict) -> list[TextContent]:
    response = api_post("/sequences/process", json={})
    response.raise_for_status()
    data = response.json()
    return [TextContent(type="text", text=data.get("message", "Processed."))]


async def handle_pause_sequence(arguments: dict) -> list[TextContent]:
    seq_id = arguments.get("sequence_id")
    if not seq_id:
        return [TextContent(type="text", text="Please provide a sequence_id.")]
    response = api_post(f"/sequences/{seq_id}/pause", json={})
    response.raise_for_status()
    return [TextContent(type="text", text=response.json().get("message", "Paused."))]


async def handle_resume_sequence(arguments: dict) -> list[TextContent]:
    seq_id = arguments.get("sequence_id")
    if not seq_id:
        return [TextContent(type="text", text="Please provide a sequence_id.")]
    response = api_post(f"/sequences/{seq_id}/resume", json={})
    response.raise_for_status()
    return [TextContent(type="text", text=response.json().get("message", "Resumed."))]


async def handle_cancel_sequence(arguments: dict) -> list[TextContent]:
    seq_id = arguments.get("sequence_id")
    if not seq_id:
        return [TextContent(type="text", text="Please provide a sequence_id.")]
    response = api_post(f"/sequences/{seq_id}/cancel", json={})
    response.raise_for_status()
    return [TextContent(type="text", text=response.json().get("message", "Cancelled."))]


async def handle_sequence_templates(arguments: dict) -> list[TextContent]:
    response = api_get("/sequences/templates/list")
    response.raise_for_status()
    data = response.json()

    text = "Follow-Up Sequence Templates:\n\n"
    for name, tmpl in data.items():
        text += f"**{name}** — {tmpl['name']}\n"
        text += f"  {tmpl['description']}\n"
        for step in tmpl["steps"]:
            text += f"    Day {step['day']}: {step['channel']} — {step['description']}\n"
        text += "\n"

    return [TextContent(type="text", text=text)]


async def handle_record_engagement(arguments: dict) -> list[TextContent]:
    seq_id = arguments.get("sequence_id")
    event = arguments.get("event")
    if not seq_id or not event:
        return [TextContent(type="text", text="Please provide sequence_id and event.")]
    response = api_post(f"/sequences/{seq_id}/engagement", json={"event": event})
    response.raise_for_status()
    data = response.json()
    return [TextContent(type="text", text=f"Recorded {event} for sequence {seq_id}. Temperature: {data.get('temperature')}, Engagement: {data.get('engagement_score', 0):.0f}/100")]


# ── Tool Registration ──

register_tool(Tool(
    name="create_follow_up_sequence",
    description="Start an automated multi-channel follow-up sequence for a lead. Sends emails, texts, calls, and postcards on a schedule. Voice: 'Start a follow-up sequence for John Smith' or 'Create a hot lead drip for the buyer from Zillow'.",
    inputSchema={
        "type": "object",
        "properties": {
            "lead_name": {"type": "string", "description": "Lead's full name"},
            "lead_email": {"type": "string", "description": "Lead's email address"},
            "lead_phone": {"type": "string", "description": "Lead's phone number"},
            "lead_source": {"type": "string", "description": "Where the lead came from (zillow, referral, website, cold)"},
            "template": {"type": "string", "description": "Sequence template: default, hot_lead, cold_lead, seller, past_client"},
            "temperature": {"type": "string", "description": "Lead temperature: hot, warm, cold"},
            "property_id": {"type": "number", "description": "Property ID if lead is about a specific property"},
            "context": {"type": "string", "description": "Additional context for personalized messages"},
        },
        "required": ["lead_name"],
    },
), handle_create_sequence)

register_tool(Tool(
    name="list_follow_up_sequences",
    description="List all follow-up sequences. Voice: 'Show me all active sequences' or 'What follow-ups are running?'.",
    inputSchema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Filter: active, paused, completed, cancelled"},
        },
    },
), handle_list_sequences)

register_tool(Tool(
    name="get_follow_up_sequence",
    description="Get details of a follow-up sequence including all touches and their status.",
    inputSchema={
        "type": "object",
        "properties": {
            "sequence_id": {"type": "number", "description": "Sequence ID"},
        },
        "required": ["sequence_id"],
    },
), handle_get_sequence)

register_tool(Tool(
    name="process_follow_up_touches",
    description="Process all due follow-up touches right now. Sends any emails, texts, or reminders that are scheduled for today or overdue.",
    inputSchema={"type": "object", "properties": {}},
), handle_process_sequences)

register_tool(Tool(
    name="pause_follow_up_sequence",
    description="Pause a follow-up sequence. No more touches will be sent until resumed.",
    inputSchema={"type": "object", "properties": {"sequence_id": {"type": "number"}}, "required": ["sequence_id"]},
), handle_pause_sequence)

register_tool(Tool(
    name="resume_follow_up_sequence",
    description="Resume a paused follow-up sequence.",
    inputSchema={"type": "object", "properties": {"sequence_id": {"type": "number"}}, "required": ["sequence_id"]},
), handle_resume_sequence)

register_tool(Tool(
    name="cancel_follow_up_sequence",
    description="Cancel a follow-up sequence. All pending touches will be skipped.",
    inputSchema={"type": "object", "properties": {"sequence_id": {"type": "number"}}, "required": ["sequence_id"]},
), handle_cancel_sequence)

register_tool(Tool(
    name="list_sequence_templates",
    description="List all available follow-up sequence templates with their steps. Voice: 'What sequence templates do we have?'.",
    inputSchema={"type": "object", "properties": {}},
), handle_sequence_templates)

register_tool(Tool(
    name="record_sequence_engagement",
    description="Record an engagement event for a sequence (email opened, reply received, call answered). This adjusts lead temperature and sequence behavior.",
    inputSchema={
        "type": "object",
        "properties": {
            "sequence_id": {"type": "number", "description": "Sequence ID"},
            "event": {"type": "string", "description": "Event: email_opened, email_replied, sms_replied, call_answered, call_voicemail"},
        },
        "required": ["sequence_id", "event"],
    },
), handle_record_engagement)
