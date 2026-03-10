"""Approval gateway — request, grant, or deny human approval for sensitive operations."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post, api_put


async def handle_request_approval(arguments: dict) -> list[TextContent]:
    """Request human approval before executing a sensitive operation."""
    payload = {
        "operation": arguments["operation"],
        "resource_type": arguments["resource_type"],
        "resource_id": arguments.get("resource_id"),
        "reason": arguments.get("reason", ""),
        "risk_level": arguments.get("risk_level", "medium"),
    }
    response = api_post("/approval/request", json=payload)
    response.raise_for_status()
    data = response.json()

    req_id = data.get("request_id", data.get("id", "unknown"))
    status = data.get("status", "pending")
    return [TextContent(
        type="text",
        text=f"Approval request #{req_id} created (status: {status}). "
             f"Operation: {payload['operation']} on {payload['resource_type']} "
             f"(risk: {payload['risk_level']}). Waiting for human decision.",
    )]


async def handle_grant_approval(arguments: dict) -> list[TextContent]:
    """Grant (approve) a pending approval request."""
    request_id = arguments.get("request_id")
    if not request_id:
        return [TextContent(type="text", text="Error: 'request_id' is required.")]

    response = api_post("/approval/grant", json={"request_id": request_id})
    response.raise_for_status()
    data = response.json()

    return [TextContent(
        type="text",
        text=f"Approval #{request_id} GRANTED. {data.get('message', 'Operation may now proceed.')}",
    )]


async def handle_deny_approval(arguments: dict) -> list[TextContent]:
    """Deny a pending approval request with a reason."""
    request_id = arguments.get("request_id")
    if not request_id:
        return [TextContent(type="text", text="Error: 'request_id' is required.")]

    reason = arguments.get("reason", "")
    response = api_post("/approval/deny", json={"request_id": request_id, "reason": reason})
    response.raise_for_status()
    data = response.json()

    return [TextContent(
        type="text",
        text=f"Approval #{request_id} DENIED. Reason: {reason or 'none given'}. "
             f"{data.get('message', '')}",
    )]


async def handle_get_audit_log(arguments: dict) -> list[TextContent]:
    """Retrieve the approval audit log."""
    limit = arguments.get("limit", 20)
    response = api_get("/approval/audit-log", params={"limit": limit})
    response.raise_for_status()
    data = response.json()

    entries = data.get("entries", data.get("log", []))
    if not entries:
        return [TextContent(type="text", text="Audit log is empty.")]

    lines = [f"Approval audit log ({len(entries)} entries):\n"]
    for e in entries:
        req_id = e.get("request_id", e.get("id", "?"))
        op = e.get("operation", "?")
        status = e.get("status", "?")
        ts = e.get("timestamp", e.get("created_at", ""))
        lines.append(f"  #{req_id} | {op} | {status} | {ts}")

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_get_autonomy_level(arguments: dict) -> list[TextContent]:
    """Get the current AI autonomy level."""
    response = api_get("/approval/autonomy-level")
    response.raise_for_status()
    data = response.json()

    level = data.get("level", "unknown")
    description = data.get("description", "")
    return [TextContent(
        type="text",
        text=f"Current autonomy level: {level}. {description}",
    )]


async def handle_set_autonomy_level(arguments: dict) -> list[TextContent]:
    """Set the AI autonomy level."""
    level = arguments.get("level", "")
    if level not in ("supervised", "semi_auto", "full_auto"):
        return [TextContent(
            type="text",
            text="Error: 'level' must be one of: supervised, semi_auto, full_auto.",
        )]

    response = api_put("/approval/autonomy-level", json={"level": level})
    response.raise_for_status()
    data = response.json()

    return [TextContent(
        type="text",
        text=f"Autonomy level set to '{level}'. {data.get('message', '')}",
    )]


# ── Tool registrations ──────────────────────────────────────────────

register_tool(
    Tool(
        name="request_approval",
        description="Request human approval before executing a sensitive or high-risk operation. "
                    "Use this whenever the autonomy level requires it, or for destructive actions like "
                    "sending contracts, making offers, or spending money. Returns a request_id to track.",
        inputSchema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "What operation needs approval (e.g. 'send_contract', 'make_offer', 'delete_property')",
                },
                "resource_type": {
                    "type": "string",
                    "description": "Type of resource involved (e.g. 'property', 'contract', 'campaign')",
                },
                "resource_id": {
                    "type": "string",
                    "description": "ID of the specific resource (optional)",
                },
                "reason": {
                    "type": "string",
                    "description": "Why this operation is being requested",
                },
                "risk_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "default": "medium",
                    "description": "Risk level of the operation",
                },
            },
            "required": ["operation", "resource_type"],
        },
    ),
    handle_request_approval,
)

register_tool(
    Tool(
        name="grant_approval",
        description="Grant (approve) a pending approval request, allowing the operation to proceed. "
                    "Only use this when the human user explicitly says to approve.",
        inputSchema={
            "type": "object",
            "properties": {
                "request_id": {
                    "type": "string",
                    "description": "The approval request ID to grant",
                },
            },
            "required": ["request_id"],
        },
    ),
    handle_grant_approval,
)

register_tool(
    Tool(
        name="deny_approval",
        description="Deny a pending approval request, blocking the operation. "
                    "Use when the human user rejects a proposed action.",
        inputSchema={
            "type": "object",
            "properties": {
                "request_id": {
                    "type": "string",
                    "description": "The approval request ID to deny",
                },
                "reason": {
                    "type": "string",
                    "description": "Why the approval is being denied",
                },
            },
            "required": ["request_id"],
        },
    ),
    handle_deny_approval,
)

register_tool(
    Tool(
        name="get_approval_audit_log",
        description="Retrieve the approval audit log showing past approval requests, grants, and denials. "
                    "Use to review what operations were approved or denied and by whom.",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 20,
                    "description": "Max number of audit log entries to return",
                },
            },
        },
    ),
    handle_get_audit_log,
)

register_tool(
    Tool(
        name="get_autonomy_level",
        description="Get the current AI autonomy level. Levels: 'supervised' (approval needed for everything), "
                    "'semi_auto' (approval only for high-risk), 'full_auto' (no approval needed). "
                    "Check this before performing sensitive operations.",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_get_autonomy_level,
)

register_tool(
    Tool(
        name="set_autonomy_level",
        description="Set the AI autonomy level. 'supervised' = approval needed for all operations, "
                    "'semi_auto' = approval only for high-risk operations, 'full_auto' = no approval needed. "
                    "Only change this when the user explicitly requests it.",
        inputSchema={
            "type": "object",
            "properties": {
                "level": {
                    "type": "string",
                    "enum": ["supervised", "semi_auto", "full_auto"],
                    "description": "The autonomy level to set",
                },
            },
            "required": ["level"],
        },
    ),
    handle_set_autonomy_level,
)
