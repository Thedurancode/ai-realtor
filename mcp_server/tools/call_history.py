"""Call History Tools - View phone call activity for properties."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get


async def handle_get_property_calls(arguments: dict) -> list[TextContent]:
    """Get all phone calls for a specific property."""
    property_id = arguments.get("property_id")
    limit = arguments.get("limit", 20)

    if not property_id:
        return [TextContent(type="text", text="Error: property_id is required")]

    response = api_get(f"/properties/{property_id}/calls", params={"limit": limit})
    response.raise_for_status()
    data = response.json()

    property_address = data.get("property_address", f"Property #{property_id}")
    calls = data.get("calls", [])
    total = data.get("total", 0)

    if not calls:
        return [TextContent(type="text", text=f"📞 No calls found for {property_address}\n\nNo phone call activity recorded yet.")]

    text = f"📞 **Call History for {property_address}**\n\n"
    text += f"Total calls: {total}\n\n"

    for i, call in enumerate(calls, 1):
        # Format call info
        provider_emoji = "🟣" if call.get("provider") == "telnyx" else "🤖"
        direction_emoji = "📤" if call.get("direction") == "outbound" else "📥"

        status = call.get("status", "unknown")
        if status == "completed":
            status_emoji = "✅"
        elif status == "in_progress":
            status_emoji = "⏳"
        elif status == "failed":
            status_emoji = "❌"
        elif status == "no_answer":
            status_emoji = "📵"
        else:
            status_emoji = "⚪"

        text += f"{i}. {provider_emoji} {direction_emoji} {status_emoji} **{status.upper()}**\n"

        if call.get("created_at"):
            text += f"   📅 {call['created_at'][:10]} at {call['created_at'][11:19]}\n"

        text += f"   📱 {call.get('phone_number', 'Unknown')}\n"

        if call.get("duration_seconds"):
            duration = call["duration_seconds"]
            mins = duration // 60
            secs = duration % 60
            text += f"   ⏱️ {mins}m {secs}s\n"

        if call.get("recording_url"):
            text += f"   🔊 Recording available\n"

        if call.get("transcription"):
            transcript = call["transcription"][:100] + "..." if len(call["transcription"]) > 100 else call["transcription"]
            text += f"   📝 Transcript: \"{transcript}\"\n"

        if call.get("summary"):
            text += f"   💡 {call['summary']}\n"

        text += "\n"

    return [TextContent(type="text", text=text)]


async def handle_get_call_recording(arguments: dict) -> list[TextContent]:
    """Get the recording URL for a specific call."""
    call_id = arguments.get("call_id")

    if not call_id:
        return [TextContent(type="text", text="Error: call_id is required")]

    response = api_get(f"/phone-calls/recording/{call_id}")
    response.raise_for_status()
    data = response.json()

    recording_url = data.get("recording_url")
    if not recording_url:
        return [TextContent(type="text", text=f"❌ No recording found for call {call_id}")]

    text = f"🔊 **Call Recording**\n\n"
    text += f"Call ID: {call_id}\n"
    text += f"Recording URL: {recording_url}\n\n"
    text += "You can use this URL to:\n"
    text += "• Play the recording in a browser\n"
    text += "• Download the audio file\n"
    text += "• Transcribe with speech-to-text services"

    return [TextContent(type="text", text=text)]


async def handle_call_summary(arguments: dict) -> list[TextContent]:
    """Get a summary of call activity for a property."""
    property_id = arguments.get("property_id")

    if not property_id:
        return [TextContent(type="text", text="Error: property_id is required")]

    response = api_get(f"/properties/{property_id}/calls", params={"limit": 100})
    response.raise_for_status()
    data = response.json()

    property_address = data.get("property_address", f"Property #{property_id}")
    calls = data.get("calls", [])

    if not calls:
        return [TextContent(type="text", text=f"📊 No call activity for {property_address}")]

    # Calculate stats
    total_calls = len(calls)
    completed_calls = [c for c in calls if c.get("status") == "completed"]
    failed_calls = [c for c in calls if c.get("status") == "failed"]
    no_answer_calls = [c for c in calls if c.get("status") == "no_answer"]

    total_duration = sum(c.get("duration_seconds", 0) for c in completed_calls)
    recordings = [c for c in calls if c.get("recording_url")]
    transcriptions = [c for c in calls if c.get("transcription")]

    # Count by provider
    vapi_calls = [c for c in calls if c.get("provider") == "vapi"]
    telnyx_calls = [c for c in calls if c.get("provider") == "telnyx"]

    text = f"📊 **Call Summary for {property_address}**\n\n"

    text += "**Overview:**\n"
    text += f"• Total calls: {total_calls}\n"
    text += f"• Completed: {len(completed_calls)} ✅\n"
    text += f"• Failed: {len(failed_calls)} ❌\n"
    text += f"• No answer: {len(no_answer_calls)} 📵\n\n"

    if total_duration > 0:
        mins = total_duration // 60
        secs = total_duration % 60
        text += f"**Total talk time:** {mins}m {secs}s\n\n"

    text += "**By Provider:**\n"
    text += f"• VAPI (AI): {len(vapi_calls)} calls\n"
    text += f"• Telnyx: {len(telnyx_calls)} calls\n\n"

    text += "**Recordings:**\n"
    text += f"• Recordings available: {len(recordings)}\n"
    text += f"• Transcriptions: {len(transcriptions)}\n\n"

    if completed_calls:
        # Get most recent call
        latest = max(completed_calls, key=lambda x: x.get("created_at", ""))
        if latest.get("created_at"):
            text += f"**Latest call:** {latest['created_at'][:10]}\n"
            if latest.get("summary"):
                text += f"Summary: {latest['summary']}\n"

    return [TextContent(type="text", text=text)]


# ── Registration ──

register_tool(
    Tool(
        name="get_property_calls",
        description=(
            "Get all phone calls for a specific property. Returns chronological list with "
            "recordings, transcriptions, summaries, and call metadata. "
            "Voice: 'Show me call history for property 5', 'What calls were made about 123 Main St?', "
            "'Get phone activity for the Hillsborough property'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "Property ID",
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum calls to return (default: 20)",
                    "default": 20,
                },
            },
            "required": ["property_id"],
        },
    ),
    handle_get_property_calls,
)

register_tool(
    Tool(
        name="get_call_recording",
        description=(
            "Get the recording URL for a specific phone call. Returns download link "
            "for the audio recording. "
            "Voice: 'Get the recording for call 123', 'Where can I listen to the call recording?', "
            "'Download call recording 456'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "call_id": {
                    "type": "number",
                    "description": "Phone call ID (from get_property_calls)",
                },
            },
            "required": ["call_id"],
        },
    ),
    handle_get_call_recording,
)

register_tool(
    Tool(
        name="call_summary",
        description=(
            "Get a summary of call activity for a property. Shows stats like total calls, "
            "completion rate, total talk time, recordings available, and breakdown by provider. "
            "Voice: 'Show me call stats for property 5', 'What's the call activity summary?', "
            "'Call analytics for 123 Main St'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "Property ID",
                },
            },
            "required": ["property_id"],
        },
    ),
    handle_call_summary,
)
