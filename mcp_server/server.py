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

    start_time = time.time()
    event_id = log_activity_event(tool_name=name, metadata=arguments)
    error_logged = False

    try:
        handler = _tool_handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        return await handler(arguments)
    except Exception as e:
        error_logged = True
        duration_ms = int((time.time() - start_time) * 1000)
        update_activity_event(event_id, status="error", duration_ms=duration_ms, error_message=str(e))
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    finally:
        if not error_logged:
            duration_ms = int((time.time() - start_time) * 1000)
            update_activity_event(event_id, status="success", duration_ms=duration_ms)
