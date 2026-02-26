"""Voice Assistant MCP tools — manage phone numbers and view call history."""
from mcp.types import Tool, TextContent
from typing import Optional

from ..server import register_tool
from ..utils.http_client import api_get, api_post, api_put, api_delete


async def handle_create_phone_number(arguments: dict) -> list[TextContent]:
    """Create a new phone number for inbound calling."""
    response = api_post("/voice-assistant/phone-numbers", arguments)
    response.raise_for_status()
    data = response.json()

    text = f"✅ Phone number created\n\n"
    text += f"Number: {data['phone_number']}\n"
    text += f"Name: {data.get('friendly_name', 'Unnamed')}\n"
    text += f"Primary: {'Yes' if data['is_primary'] else 'No'}\n"
    text += f"Status: {'Active' if data['is_active'] else 'Inactive'}\n"
    text += f"Capabilities: "
    caps = []
    if data['can_receive_calls']:
        caps.append("inbound")
    if data['can_make_calls']:
        caps.append("outbound")
    text += ", ".join(caps)

    return [TextContent(type="text", text=text)]


async def handle_list_phone_numbers(arguments: dict) -> list[TextContent]:
    """List all phone numbers."""
    response = api_get("/voice-assistant/phone-numbers")
    response.raise_for_status()
    numbers = response.json()

    if not numbers:
        return [TextContent(type="text", text="No phone numbers configured")]

    text = f"📞 Phone Numbers ({len(numbers)})\n\n"
    for num in numbers:
        primary = " ⭐" if num['is_primary'] else ""
        status = "🟢" if num['is_active'] else "🔴"
        text += f"{status} {num['phone_number']}{primary}\n"
        if num.get('friendly_name'):
            text += f"   Name: {num['friendly_name']}\n"
        text += f"   Calls: {num['total_calls']}, Minutes: {num['total_minutes']}\n"
        text += "\n"

    return [TextContent(type="text", text=text.strip())]


async def handle_set_primary_number(arguments: dict) -> list[TextContent]:
    """Set a phone number as primary."""
    phone_id = arguments.get("phone_id")
    response = api_post(f"/voice-assistant/phone-numbers/{phone_id}/set-primary")
    response.raise_for_status()

    return [TextContent(type="text", text=f"✅ Phone number {phone_id} set as primary")]


async def handle_list_calls(arguments: dict) -> list[TextContent]:
    """View call history."""
    params = {}
    if arguments.get("direction"):
        params["direction"] = arguments["direction"]
    if arguments.get("intent"):
        params["intent"] = arguments["intent"]
    if arguments.get("property_id"):
        params["property_id"] = arguments["property_id"]

    response = api_get("/voice-assistant/phone-calls", params=params)
    response.raise_for_status()
    data = response.json()

    if not data["calls"]:
        return [TextContent(type="text", text="No calls found")]

    text = f"📞 Call History (showing {len(data['calls'])} of {data['total']})\n\n"

    for call in data["calls"]:
        direction_icon = "📥" if call["direction"] == "inbound" else "📤"
        status_emoji = {
            "completed": "✅",
            "in_progress": "🔄",
            "failed": "❌",
            "no_answer": "🔕"
        }.get(call["status"], "⚪")

        text += f"{direction_icon} {status_emoji} {call['phone_number']}\n"
        text += f"   Time: {call['created_at']}\n"
        if call.get("intent"):
            text += f"   Intent: {call['intent']}\n"
        if call.get("outcome"):
            text += f"   Outcome: {call['outcome']}\n"
        if call.get("duration_seconds"):
            text += f"   Duration: {call['duration_seconds']}s\n"
        text += "\n"

    return [TextContent(type="text", text=text.strip())]


async def handle_get_call_transcript(arguments: dict) -> list[TextContent]:
    """Get call transcript and summary."""
    call_id = arguments.get("call_id")

    # Get call details
    response = api_get(f"/voice-assistant/phone-calls/{call_id}")
    response.raise_for_status()
    call = response.json()

    # Get transcript
    response = api_get(f"/voice-assistant/phone-calls/transcription/{call_id}")
    response.raise_for_status()
    data = response.json()

    text = f"📞 Call Details\n\n"
    text += f"From: {call['phone_number']}\n"
    text += f"Direction: {call['direction']}\n"
    text += f"Status: {call['status']}\n"
    text += f"Duration: {call.get('duration_seconds', 'N/A')}s\n"
    if call.get('intent'):
        text += f"Intent: {call['intent']}\n"
    if call.get('outcome'):
        text += f"Outcome: {call['outcome']}\n"

    if data.get('summary'):
        text += f"\n📝 Summary:\n{data['summary']}\n"

    if data.get('transcription'):
        text += f"\n💬 Transcript:\n{data['transcription']}\n"

    return [TextContent(type="text", text=text)]


async def handle_get_call_analytics(arguments: dict) -> list[TextContent]:
    """Get call analytics overview."""
    response = api_get("/voice-assistant/phone-calls/analytics/overview")
    response.raise_for_status()
    data = response.json()

    text = f"📊 Call Analytics\n\n"
    text += f"Total Calls: {data['total_calls']}\n"
    text += f"  • Inbound: {data['inbound_calls']}\n"
    text += f"  • Outbound: {data['outbound_calls']}\n\n"

    text += f"Completed: {data['completed_calls']}\n"
    text += f"Missed: {data['missed_calls']}\n"
    text += f"Completion Rate: {data['completion_rate']}%\n\n"

    text += f"Total Duration: {data['total_duration_minutes']} min\n"
    text += f"Total Cost: ${data['total_cost']:.2f}\n\n"

    if data.get('intents'):
        text += f"Intents:\n"
        for intent, count in data['intents'].items():
            text += f"  • {intent}: {count}\n"

    if data.get('outcomes'):
        text += f"\nOutcomes:\n"
        for outcome, count in data['outcomes'].items():
            text += f"  • {outcome}: {count}\n"

    return [TextContent(type="text", text=text)]


async def handle_get_property_call_stats(arguments: dict) -> list[TextContent]:
    """Get call statistics grouped by property."""
    response = api_get("/voice-assistant/phone-calls/analytics/by-property")
    response.raise_for_status()
    data = response.json()

    if not data["properties"]:
        return [TextContent(type="text", text="No calls recorded for properties yet")]

    text = f"🏠 Property Call Statistics\n\n"

    for prop in data["properties"]:
        text += f"Property #{prop['property_id']}: {prop['address']}\n"
        text += f"  Total Calls: {prop['total_calls']}\n"
        text += f"  Inbound: {prop['inbound_calls']}, Outbound: {prop['outbound_calls']}\n"
        text += f"  Unique Callers: {prop['unique_callers']}\n"
        if prop['viewings_scheduled'] > 0:
            text += f"  Viewings Scheduled: {prop['viewings_scheduled']}\n"
        if prop['offers_created'] > 0:
            text += f"  Offers Created: {prop['offers_created']}\n"
        text += "\n"

    return [TextContent(type="text", text=text.strip())]


# Register all tools
register_tool(
    Tool(
        name="create_phone_number",
        description=(
            "Create a new phone number for inbound AI calling. "
            "Voice: 'Create a phone number for inbound calls', "
            "'Add a new phone line', 'Set up a virtual number'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number in E.164 format (e.g., +14155551234)",
                },
                "friendly_name": {
                    "type": "string",
                    "description": "Display name (e.g., Main Line, Listings Hotline)",
                },
                "greeting_message": {
                    "type": "string",
                    "description": "Custom greeting (e.g., Thanks for calling Emprezario)",
                },
                "is_primary": {
                    "type": "boolean",
                    "description": "Set as primary number",
                },
            },
            "required": ["phone_number"],
        },
    ),
    handle_create_phone_number,
)

register_tool(
    Tool(
        name="list_phone_numbers",
        description=(
            "List all configured phone numbers with stats. "
            "Voice: 'Show me my phone numbers', 'List my phone lines'"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_list_phone_numbers,
)

register_tool(
    Tool(
        name="set_primary_phone_number",
        description=(
            "Set a phone number as the primary number. "
            "Voice: 'Set this number as primary', 'Make this my main line'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "phone_id": {
                    "type": "number",
                    "description": "Phone number ID from list_phone_numbers",
                },
            },
            "required": ["phone_id"],
        },
    ),
    handle_set_primary_number,
)

register_tool(
    Tool(
        name="get_call_history",
        description=(
            "View phone call history. Voice: 'Show me recent calls', "
            "'Get call history', 'Show missed calls'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["inbound", "outbound"],
                    "description": "Filter by direction",
                },
                "intent": {
                    "type": "string",
                    "description": "Filter by intent (property_inquiry, schedule_viewing, etc.)",
                },
                "property_id": {
                    "type": "number",
                    "description": "Filter by property",
                },
            },
        },
    ),
    handle_list_calls,
)

register_tool(
    Tool(
        name="get_call_transcript",
        description=(
            "Get full call transcript and AI summary. "
            "Voice: 'Show me the transcript for call 5', 'What was said in call 3?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "call_id": {
                    "type": "number",
                    "description": "Call ID from get_call_history",
                },
            },
            "required": ["call_id"],
        },
    ),
    handle_get_call_transcript,
)

register_tool(
    Tool(
        name="get_call_analytics",
        description=(
            "Get call analytics overview with stats. "
            "Voice: 'Show call analytics', 'How are my calls performing?', 'Call stats'"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_get_call_analytics,
)

register_tool(
    Tool(
        name="get_property_call_stats",
        description=(
            "Get call statistics grouped by property. "
            "Voice: 'Which properties get the most calls?', 'Property call stats'"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_get_property_call_stats,
)
