"""Workflow template MCP tools for executing multi-step voice-first operations."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_execute_workflow(arguments: dict) -> list[TextContent]:
    payload = {
        "template_name": arguments["workflow"],
        "property_id": arguments.get("property_id"),
        "property_query": arguments.get("property_query"),
        "session_id": arguments.get("session_id", "mcp_session"),
        "execution_mode": arguments.get("execution_mode"),
        "confirm_high_risk": arguments.get("confirm_high_risk", False),
    }
    response = api_post("/workflows/execute", json=payload)
    response.raise_for_status()
    result = response.json()

    workflow_name = result.get("workflow", arguments["workflow"])
    status = result.get("status", "unknown")

    text = f"Workflow '{workflow_name}' - {status}\n\n"

    goal_result = result.get("result", {})

    # Show checkpoints
    checkpoints = goal_result.get("checkpoints", [])
    if checkpoints:
        text += "Steps completed:\n"
        for cp in checkpoints:
            icon = "+" if cp.get("status") == "completed" else "!" if cp.get("status") == "failed" else "?"
            text += f"  [{icon}] {cp.get('title', cp.get('action', ''))}: {cp.get('message', '')}\n"
        text += "\n"

    # Show final summary
    summary = goal_result.get("final_summary", "")
    if summary:
        text += f"{summary}\n"

    # Show if blocked
    if goal_result.get("needs_confirmation"):
        text += "\nThis workflow requires confirmation for a high-risk step. "
        text += "Re-run with confirm_high_risk=true to proceed."

    return [TextContent(type="text", text=text)]


async def handle_list_workflows(arguments: dict) -> list[TextContent]:
    response = api_get("/workflows/templates")
    response.raise_for_status()
    templates = response.json()

    if not templates:
        return [TextContent(type="text", text="No workflow templates available.")]

    text = f"{len(templates)} workflow template(s) available:\n\n"
    for t in templates:
        text += f"  {t['name']}: {t['description']}\n"
        text += f"    Trigger phrases: {', '.join(t['trigger_phrases'][:3])}\n\n"
    return [TextContent(type="text", text=text)]


register_tool(
    Tool(
        name="execute_workflow",
        description="Execute a pre-defined multi-step workflow with a single command. "
                    "Available workflows: new_lead, ready_to_close, market_analysis, cold_call_owner, contract_cleanup. "
                    "Voice: 'Run the new lead workflow for property 5' or 'Get property 5 ready to close'",
        inputSchema={
            "type": "object",
            "properties": {
                "workflow": {
                    "type": "string",
                    "description": "Workflow template name",
                    "enum": ["new_lead", "ready_to_close", "market_analysis", "cold_call_owner", "contract_cleanup"],
                },
                "property_id": {"type": "integer", "description": "Target property ID"},
                "property_query": {"type": "string", "description": "Search for property by address (alternative to property_id)"},
                "session_id": {"type": "string", "default": "mcp_session"},
                "execution_mode": {
                    "type": "string", "enum": ["safe", "autonomous"],
                    "description": "safe = confirm risky steps, autonomous = auto-execute all",
                },
                "confirm_high_risk": {"type": "boolean", "default": False, "description": "Confirm high-risk steps"},
            },
            "required": ["workflow"],
        },
    ),
    handle_execute_workflow,
)

register_tool(
    Tool(
        name="list_workflows",
        description="List all available workflow templates with descriptions and trigger phrases. "
                    "Voice: 'What workflows are available?'",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_list_workflows,
)
