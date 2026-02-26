"""MCP Server instance and tool registry."""
import time
from typing import Any, Callable

from mcp.server import Server
from mcp.types import Tool, TextContent

# Global server instance
app = Server("property-management")

# Tool registry - modules populate this at import time
_tool_definitions: list[Tool] = []
_tool_handlers: dict[str, Callable] = {}


def register_tool(tool: Tool, handler: Callable):
    """Register a tool definition and its async handler."""
    _tool_definitions.append(tool)
    _tool_handlers[tool.name] = handler


@app.list_tools()
async def list_tools() -> list[Tool]:
    return _tool_definitions


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    from .utils.activity_logging import log_activity_event, update_activity_event
    from .utils.context_enrichment import enrich_response
    from .utils.http_client import api_post

    start_time = time.time()
    event_id = log_activity_event(tool_name=name, metadata=arguments)
    error_logged = False

    try:
        handler = _tool_handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        result = await handler(arguments)

        # Auto-inject conversation context into response
        try:
            result = enrich_response(
                tool_name=name,
                arguments=arguments or {},
                result=result,
            )
        except Exception:
            pass  # Never let context enrichment break the main response

        # Log to conversation history
        duration_ms = int((time.time() - start_time) * 1000)
        _log_conversation(name, arguments, result, success=True, duration_ms=duration_ms)

        return result
    except Exception as e:
        error_logged = True
        duration_ms = int((time.time() - start_time) * 1000)
        update_activity_event(event_id, status="error", duration_ms=duration_ms, error_message=str(e))
        _log_conversation(name, arguments, None, success=False, duration_ms=duration_ms, error=str(e))
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    finally:
        if not error_logged:
            duration_ms = int((time.time() - start_time) * 1000)
            update_activity_event(event_id, status="success", duration_ms=duration_ms)


def _log_conversation(tool_name: str, arguments: Any, result: list[TextContent] | None, success: bool, duration_ms: int, error: str = None):
    """Log tool call to conversation history."""
    from .utils.http_client import api_post

    # Skip logging conversation history tools to avoid recursion
    if tool_name in ("get_conversation_history", "what_did_we_discuss", "clear_conversation_history", "get_property_history"):
        return

    try:
        # Create input summary
        input_summary = _summarize_input(tool_name, arguments)

        # Create output summary
        if success and result:
            output_text = result[0].text if result else ""
            output_summary = _summarize_output(tool_name, output_text)
        else:
            output_summary = f"Failed: {error}" if error else "Failed"

        # Extract property_id from arguments if present
        property_id = None
        if isinstance(arguments, dict):
            property_id = arguments.get("property_id")

        payload = {
            "session_id": "mcp_session",
            "tool_name": tool_name,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "success": success,
            "duration_ms": duration_ms,
        }
        if property_id is not None:
            payload["property_id"] = property_id

        api_post("/context/history/log", json=payload)
    except Exception:
        pass  # Don't fail the main operation if logging fails


def _summarize_input(tool_name: str, arguments: Any) -> str:
    """Create a human-readable summary of tool input."""
    if not arguments:
        return f"Called {tool_name}"

    # Property tools
    if tool_name == "list_properties":
        return f"List properties (limit: {arguments.get('limit', 10)})"
    if tool_name == "get_property":
        return f"Get property #{arguments.get('property_id')}"
    if tool_name == "create_property":
        return f"Create property at {arguments.get('address')}"
    if tool_name == "enrich_property":
        return f"Enrich property #{arguments.get('property_id')} with Zillow"
    if tool_name == "skip_trace_property":
        return f"Skip trace property #{arguments.get('property_id')}"

    # Offer tools
    if tool_name == "create_offer":
        return f"Create ${arguments.get('offer_price', 0):,.0f} offer on property #{arguments.get('property_id')}"
    if tool_name == "list_offers":
        return "List all offers"

    # Contract tools
    if tool_name == "list_contracts":
        return "List contracts"
    if tool_name == "check_property_contract_readiness":
        return f"Check if property #{arguments.get('property_id')} is ready to close"

    # Notification tools
    if tool_name == "send_notification":
        return f"Send notification: {arguments.get('title')}"

    # Campaign tools
    if tool_name == "create_voice_campaign":
        return f"Create campaign '{arguments.get('name')}' ({arguments.get('call_purpose')})"
    if tool_name == "start_voice_campaign":
        return f"Start campaign #{arguments.get('campaign_id')}"
    if tool_name == "pause_voice_campaign":
        return f"Pause campaign #{arguments.get('campaign_id')}"
    if tool_name == "get_campaign_status":
        return f"Get status for campaign #{arguments.get('campaign_id')}"
    if tool_name == "list_voice_campaigns":
        return f"List campaigns (status: {arguments.get('status', 'all')})"
    if tool_name == "add_campaign_targets":
        return f"Add targets to campaign #{arguments.get('campaign_id')}"

    # Calendar tools
    if tool_name == "connect_calendar":
        return "Connect Google Calendar"
    if tool_name == "create_calendar_event":
        return f"Create calendar event: {arguments.get('title')}"
    if tool_name == "list_calendar_events":
        return f"List calendar events (days: {arguments.get('days', 7)})"
    if tool_name == "sync_to_calendar":
        return "Sync to Google Calendar"
    if tool_name == "list_calendars":
        return "List connected calendars"
    if tool_name == "disconnect_calendar":
        return f"Disconnect calendar #{arguments.get('connection_id')}"
    if tool_name == "update_calendar_event":
        return f"Update calendar event #{arguments.get('event_id')}"
    if tool_name == "delete_calendar_event":
        return f"Delete calendar event #{arguments.get('event_id')}"

    # Smart calendar tools
    if tool_name == "check_calendar_conflicts":
        return f"Check calendar conflicts for {arguments.get('start_time', 'proposed time')}"
    if tool_name == "suggest_meeting_time":
        duration = arguments.get('duration_minutes', 60)
        return f"Suggest meeting time ({duration} min)"
    if tool_name == "analyze_schedule":
        days = arguments.get('days', 7)
        return f"Analyze schedule ({days} days)"

    # AI calendar optimization tools
    if tool_name == "get_calendar_insights":
        days = arguments.get('days', 30)
        return f"Get calendar insights ({days} days)"
    if tool_name == "find_optimal_time":
        event_type = arguments.get('event_type', 'meeting')
        return f"Find optimal time for {event_type}"
    if tool_name == "predict_meeting_success":
        day = arguments.get('day_of_week', 'weekday')
        hour = arguments.get('hour', 12)
        return f"Predict success for {day} at {hour}:00"
    if tool_name == "optimize_schedule":
        return "Optimize schedule with AI"

    # Q&A call tools
    if tool_name == "qa_call":
        questions_count = len(arguments.get('questions', []))
        return f"Q&A call with {questions_count} questions"
    if tool_name == "get_call_status":
        return f"Check call status {arguments.get('call_id')}"
    if tool_name == "schedule_qa_call":
        return f"Schedule Q&A call for {arguments.get('scheduled_time', 'later')}"
    if tool_name == "batch_qa_calls":
        contacts_count = len(arguments.get('contacts', []))
        return f"Batch Q&A calls to {contacts_count} contacts"

    # Call history tools
    if tool_name == "get_property_calls":
        return f"View call history for property {arguments.get('property_id')}"
    if tool_name == "get_call_recording":
        return f"Get recording for call {arguments.get('call_id')}"
    if tool_name == "call_summary":
        return f"Call summary for property {arguments.get('property_id')}"

    # Default
    return f"Called {tool_name}"


def _summarize_output(tool_name: str, output_text: str) -> str:
    """Create a human-readable summary of tool output."""
    # Truncate long outputs
    if len(output_text) > 200:
        return output_text[:200] + "..."
    return output_text
