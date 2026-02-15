"""Bulk Operations MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_execute_bulk_operation(arguments: dict) -> list[TextContent]:
    """Execute a bulk operation across multiple properties."""
    operation = arguments.get("operation")
    if not operation:
        return [TextContent(type="text", text="Please provide an operation (enrich, skip_trace, attach_contracts, generate_recaps, update_status, check_compliance).")]

    body = {"operation": operation}

    property_ids = arguments.get("property_ids")
    if property_ids:
        body["property_ids"] = property_ids

    filters = arguments.get("filters")
    if filters:
        body["filters"] = filters

    params = arguments.get("params")
    if params:
        body["params"] = params

    response = api_post("/bulk/execute", json=body)
    if response.status_code == 400:
        return [TextContent(type="text", text=f"Error: {response.json().get('detail', 'Bad request')}")]
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "Bulk operation complete.")
    results = data.get("results", [])

    text = f"{voice}\n\n"
    for r in results:
        icon = "✓" if r["status"] == "success" else "○" if r["status"] == "skipped" else "✗"
        text += f"  {icon} Property #{r['property_id']} {r['address']} — {r['detail']}\n"

    return [TextContent(type="text", text=text.strip())]


async def handle_list_bulk_operations(arguments: dict) -> list[TextContent]:
    """List available bulk operations."""
    response = api_get("/bulk/operations")
    response.raise_for_status()
    data = response.json()

    ops = data.get("operations", [])
    text = f"AVAILABLE BULK OPERATIONS ({len(ops)}):\n\n"
    for op in ops:
        text += f"  {op['name']} — {op['description']}\n"
        if op.get("params"):
            for k, v in op["params"].items():
                text += f"    param: {k} — {v}\n"
        text += "\n"

    return [TextContent(type="text", text=text.strip())]


# ── Registration ──

register_tool(
    Tool(
        name="execute_bulk_operation",
        description=(
            "Execute an operation across multiple properties at once. "
            "Supported: enrich, skip_trace, attach_contracts, generate_recaps, update_status, check_compliance. "
            "Select properties by IDs and/or filters (city, status, property_type, min_price, max_price, bedrooms). "
            "Voice: 'Enrich all Miami properties', 'Skip trace properties 1 through 5', "
            "'Generate recaps for all available properties', 'Update all pending properties to sold'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["enrich", "skip_trace", "attach_contracts", "generate_recaps", "update_status", "check_compliance"],
                    "description": "The operation to execute",
                },
                "property_ids": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Explicit property IDs to operate on",
                },
                "filters": {
                    "type": "object",
                    "description": "Dynamic property filters (city, status, property_type, min_price, max_price, bedrooms)",
                    "properties": {
                        "city": {"type": "string"},
                        "status": {"type": "string", "enum": ["available", "pending", "sold", "rented", "off_market"]},
                        "property_type": {"type": "string"},
                        "min_price": {"type": "number"},
                        "max_price": {"type": "number"},
                        "bedrooms": {"type": "number"},
                    },
                },
                "params": {
                    "type": "object",
                    "description": "Operation-specific params (e.g. force: true, status: 'sold')",
                },
            },
            "required": ["operation"],
        },
    ),
    handle_execute_bulk_operation,
)

register_tool(
    Tool(
        name="list_bulk_operations",
        description=(
            "List all available bulk operations with descriptions and parameters. "
            "Voice: 'What bulk operations are available?', 'What can I do in bulk?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_list_bulk_operations,
)
