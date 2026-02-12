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
    from .utils.http_client import api_post

    start_time = time.time()
    event_id = log_activity_event(tool_name=name, metadata=arguments)
    error_logged = False

    try:
        handler = _tool_handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        result = await handler(arguments)

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
    if tool_name in ("get_conversation_history", "what_did_we_discuss", "clear_conversation_history"):
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

        api_post("/context/history/log", json={
            "session_id": "mcp_session",
            "tool_name": tool_name,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "success": success,
            "duration_ms": duration_ms,
        })
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

    # Default
    return f"Called {tool_name}"


def _summarize_output(tool_name: str, output_text: str) -> str:
    """Create a human-readable summary of tool output."""
    # Truncate long outputs
    if len(output_text) > 200:
        return output_text[:200] + "..."
    return output_text
