"""AI-Powered Phone Q&A - Make calls to get answers and information."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_qa_call(arguments: dict) -> list[TextContent]:
    """Make a phone call to ask questions and get answers."""
    phone = arguments.get("phone")
    questions = arguments.get("questions", [])
    property_id = arguments.get("property_id")
    contact_id = arguments.get("contact_id")
    property_context = arguments.get("property_context", True)
    provider = arguments.get("provider", "vapi")  # "vapi" or "telnyx"

    # If contact_id provided, get their phone
    if contact_id and not phone:
        try:
            contact_response = api_get(f"/contacts/{contact_id}")
            contact_response.raise_for_status()
            contact_data = contact_response.json()
            phone = contact_data.get("phone")
        except:
            pass

    if not phone:
        return [TextContent(type="text", text="Error: No phone number provided. Please provide a phone number.")]

    # Build call script
    if not questions:
        return [TextContent(type="text", text="Error: Please provide at least one question to ask.")]

    # Build script with context
    script = "Hello, this is your real estate agent calling. I have a few quick questions:\n\n"
    for i, question in enumerate(questions, 1):
        script += f"{i}. {question}\n"
    script += "\nThank you for your time!"

    # Route to appropriate provider
    if provider == "telnyx":
        # Use Telnyx API
        call_request = {
            "to": phone,
            "script": script,
            "property_id": property_id,
            "questions": questions,
            "detect_machine": arguments.get("detect_machine", True),
            "record_call": arguments.get("record_call", True),
        }
        response = api_post("/telnyx/calls", json=call_request)
    else:
        # Use VAPI (default)
        call_request = {
            "phone": phone,
            "name": f"Q&A Call about " + (arguments.get("call_about", "Property") if arguments.get("call_about") else "Property"),
            "script": script,
        }

        # Add property context if available
        if property_id and property_context:
            try:
                prop_response = api_get(f"/properties/{property_id}")
                prop_response.raise_for_status()
                prop_data = prop_response.json()

                # Enhance script with property context
                call_request["script"] = (
                    f"Hello, this is your real estate agent calling about the property at "
                    f"{prop_data.get('address', '')}, {prop_data.get('city', '')}. "
                    f"I have a few quick questions:\n\n"
                )
                for i, question in enumerate(questions, 1):
                    call_request["script"] += f"{i}. {question}\n"
                call_request["script"] += "\nThank you for your time!"
            except:
                pass

    # Make the call via the selected provider
    if provider == "telnyx":
        # For Telnyx, property context is already in the script
        if property_id and property_context:
            try:
                prop_response = api_get(f"/properties/{property_id}")
                prop_response.raise_for_status()
                prop_data = prop_response.json()

                # Enhance script with property context
                call_request["script"] = (
                    f"Hello, this is your real estate agent calling about the property at "
                    f"{prop_data.get('address', '')}, {prop_data.get('city', '')}. "
                    f"I have a few quick questions:\n\n"
                )
                for i, question in enumerate(questions, 1):
                    call_request["script"] += f"{i}. {question}\n"
                call_request["script"] += "\nThank you for your time!"
            except:
                pass

    # Make the HTTP request
    if provider == "telnyx":
        response = api_post("/telnyx/calls", json=call_request)
    else:
        response = api_post("/calls/voice", json=call_request)

    response.raise_for_status()
    call_data = response.json()

    if call_data.get("error"):
        return [TextContent(type="text", text=f"Error: {call_data['error']}")]

    # Handle different response formats from providers
    if provider == "telnyx":
        call_id = call_data.get("call_id") or call_data.get("call_control_id")
        phone_number = call_data.get("to", phone)
    else:
        call_id = call_data.get("call_id")
        phone_number = call_data.get("phone_number", phone)

    text = f"📞 **Initiated Q&A Call** ({provider.upper()})\n\n"
    text += f"Calling: {phone_number}\n"
    text += f"Call ID: {call_id}\n\n"
    text += f"**Questions:**\n"
    for i, question in enumerate(questions, 1):
        text += f"{i}. {question}\n"
    text += "\n"
    text += "📝 Transcript will be available once the call completes.\n"
    text += f"\n💡 Use 'get_call_status {call_id}' to check if the call has completed."

    return [TextContent(type="text", text=text)]


async def handle_get_call_status(arguments: dict) -> list[TextContent]:
    """Check the status of a previous Q&A call and get the transcript."""
    call_id = arguments.get("call_id")
    provider = arguments.get("provider", "vapi")  # "vapi" or "telnyx"

    # Route to appropriate provider endpoint
    if provider == "telnyx":
        response = api_get(f"/telnyx/calls/{call_id}")
    else:
        response = api_get(f"/calls/{call_id}")

    response.raise_for_status()
    data = response.json()

    if data.get("error"):
        return [TextContent(type="text", text=f"Error: {data['error']}")]

    status = data.get("status", "unknown")
    transcript = data.get("transcript", "")
    analysis = data.get("analysis", {})
    call = data.get("call", {})

    text = f"📞 **Call Status: {status.upper()}**\n\n"

    if status == "in_progress":
        text += "⏳ Call is in progress. Check back in a few minutes.\n"
    elif status == "completed":
        text += "✅ Call completed successfully.\n\n"

        if transcript:
            text += "**Transcript:**\n"
            # Show first 500 chars of transcript
            transcript_preview = transcript[:500] + "..." if len(transcript) > 500 else transcript
            text += f"{transcript_preview}\n\n"

        if analysis:
            text += "**Key Information Extracted:**\n"
            for key, value in analysis.items():
                if value:
                    text += f"• **{key}**: {value}\n"

        if call.get("duration_seconds"):
            duration = call["duration_seconds"]
            text += f"\n📊 Call Duration: {duration} seconds"
    elif status == "failed":
        text += "❌ Call failed.\n"
        error_msg = data.get("error_message", "Unknown error")
        text += f"Error: {error_msg}"
    elif status == "no_answer":
        text += "📵 No answer. The call went to voicemail."

    # Add call metadata
    if call.get("started_at"):
        text += f"\n🕒 Started: {call['started_at']}"

    return [TextContent(type="text", text=text)]


async def handle_schedule_qa_call(arguments: dict) -> list[TextContent]:
    """Schedule a Q&A call for a specific time."""
    phone = arguments.get("phone")
    questions = arguments.get("questions", [])
    scheduled_time = arguments.get("scheduled_time")
    property_id = arguments.get("property_id")

    if not phone:
        return [TextContent(type="text", text="Error: Phone number is required.")]

    # Create scheduled task for the call
    task_request = {
        "title": arguments.get("title", "Q&A Call"),
        "scheduled_at": scheduled_time,
        "action": "make_qa_call",
        "metadata": {
            "phone": phone,
            "questions": questions,
            "property_id": property_id,
        }
    }

    response = api_post("/scheduled-tasks/", json=task_request)
    response.raise_for_status()
    task_data = response.json()

    if task_data.get("error"):
        return [TextContent(type="text", text=f"Error: {task_data['error']}")]

    text = f"⏰ **Q&A Call Scheduled**\n\n"
    text += f"Phone: {phone}\n"
    text += f"Scheduled: {scheduled_time}\n"
    text += f"Task ID: {task_data.get('id')}\n\n"
    text += f"**Questions to ask:**\n"
    for i, question in enumerate(questions, 1):
        text += f"{i}. {question}\n"
    text += "\n✓ You'll be notified when it's time to make the call."

    return [TextContent(type="text", text=text)]


async def handle_batch_qa_calls(arguments: dict) -> list[TextContent]:
    """Make Q&A calls to multiple contacts."""
    contacts = arguments.get("contacts", [])  # List of {phone, questions: []}
    property_id = arguments.get("property_id")

    if not contacts:
        return [TextContent(type="text", text="Error: No contacts provided.")]

    results = []
    for contact in contacts:
        phone = contact.get("phone")
        questions = contact.get("questions", [])

        if not phone or not questions:
            results.append({"phone": phone, "error": "Missing phone or questions"})
            continue

        # Make individual call
        response = api_post("/calls/voice", json={
            "phone": phone,
            "name": f"Q&A Call - {contact.get('name', 'Contact')}",
            "script": f"Hi, I have some questions: {'; '.join(questions)}",
        })

        response.raise_for_status()
        call_data = response.json()

        if call_data.get("error"):
            results.append({"phone": phone, "error": call_data["error"]})
        else:
            results.append({
                "phone": phone,
                "call_id": call_data.get("call_id"),
                "status": "initiated"
            })

    text = f"📞 **Batch Q&A Calls Initiated**\n\n"
    text += f"Total calls: {len(contacts)}\n\n"

    for i, result in enumerate(results, 1):
        phone = result.get("phone", "Unknown")
        if result.get("error"):
            text += f"{i}. {phone}: ❌ {result['error']}\n"
        else:
            text += f"{i}. {phone}: ✅ Call ID {result.get('call_id')}\n"

    text += f"\n💡 Use 'get_call_status <call_id>' to check results."

    return [TextContent(type="text", text=text)]


# ── Registration ──

register_tool(
    Tool(
        name="qa_call",
        description=(
            "Make an automated phone call to ask questions and get answers. "
            "Supports both VAPI AI and Telnyx providers for natural conversations. "
            "Telnyx offers answering machine detection and call recording. "
            "Voice: 'Call the seller at 555-1234 and ask if they're flexible on price', "
            "'Phone the buyer using Telnyx and ask their preferred move-in date', "
            "'Call the inspector with VAPI and ask about any issues with the foundation'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Phone number to call",
                },
                "questions": {
                    "type": "array",
                    "description": "List of questions to ask",
                    "items": {"type": "string"},
                },
                "property_id": {
                    "type": "number",
                    "description": "Property ID for context (optional)",
                },
                "contact_id": {
                    "type": "number",
                    "description": "Contact ID to get phone from (optional)",
                },
                "call_about": {
                    "type": "string",
                    "description": "What the call is about (for script intro)",
                    "default": "Property",
                },
                "property_context": {
                    "type": "boolean",
                    "description": "Include property details in script (default: true)",
                    "default": True,
                },
                "provider": {
                    "type": "string",
                    "description": "Call provider (vapi or telnyx, default: vapi)",
                    "enum": ["vapi", "telnyx"],
                    "default": "vapi",
                },
                "detect_machine": {
                    "type": "boolean",
                    "description": "Enable answering machine detection (telnyx only)",
                    "default": True,
                },
                "record_call": {
                    "type": "boolean",
                    "description": "Enable call recording (telnyx only)",
                    "default": True,
                },
            },
            "required": ["phone", "questions"],
        },
    ),
    handle_qa_call,
)

register_tool(
    Tool(
        name="get_call_status",
        description=(
            "Check the status of a previous Q&A call and get the transcript. "
            "Returns status, transcript, and AI-extracted answers. "
            "Voice: "What's the status of call 12345?", "Get the transcript of the seller call", "
            "'Did the buyer answer about their move-in date?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "call_id": {
                    "type": "string",
                    "description": "Call ID to check",
                },
                "provider": {
                    "type": "string",
                    "description": "Call provider (vapi or telnyx, default: vapi)",
                    "enum": ["vapi", "telnyx"],
                    "default": "vapi",
                },
            },
            "required": ["call_id"],
        },
    ),
    handle_get_call_status,
)

register_tool(
    Tool(
        name="schedule_qa_call",
        description=(
            "Schedule a Q&A call for a specific time. Creates a scheduled task that "
            "will trigger the call automatically. "
            "Voice: "Schedule a call to the seller tomorrow at 10am", "
            "'Set up a reminder to call the buyer on Friday afternoon', "
            "'Remind me to phone the inspector next Monday morning'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Phone number to call",
                },
                "questions": {
                    "type": "array",
                    "description": "List of questions to ask",
                    "items": {"type": "string"},
                },
                "scheduled_time": {
                    "type": "string",
                    "description": "When to make the call (ISO format or natural language)",
                },
                "title": {
                    "type": "string",
                    "description": "Title for the scheduled task",
                    "default": "Q&A Call",
                },
                "property_id": {
                    "type": "number",
                    "description": "Property ID (optional)",
                },
            },
            "required": ["phone", "questions", "scheduled_time"],
        },
    ),
    handle_schedule_qa_call,
)

register_tool(
    Tool(
        name="batch_qa_calls",
        description=(
            "Make Q&A calls to multiple contacts at once. Useful for gathering information "
            "from multiple parties simultaneously. "
            "Voice: "Call all parties for property 5 and ask about availability", "
            "'Phone the buyer and seller to confirm closing time', "
            "'Survey all contacts about their preferred meeting time'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "contacts": {
                    "type": "array",
                    "description": "List of contacts with phone numbers and questions",
                    "items": {
                        "type": "object",
                        "properties": {
                            "phone": {"type": "string"},
                            "name": {"type": "string"},
                            "questions": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "property_id": {
                    "type": "number",
                    "description": "Property ID for context (optional)",
                },
            },
            "required": ["contacts"],
        },
    ),
    handle_batch_qa_calls,
)
