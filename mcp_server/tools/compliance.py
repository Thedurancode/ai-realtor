"""Compliance MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_run_compliance_check(arguments: dict) -> list[TextContent]:
    """Run a compliance check on a property."""
    property_id = arguments.get("property_id")
    check_type = arguments.get("check_type", "full")
    agent_id = arguments.get("agent_id")

    if not property_id:
        return [TextContent(type="text", text="Error: property_id is required.")]

    params = {"check_type": check_type}
    if agent_id:
        params["agent_id"] = agent_id

    response = api_post(f"/compliance/properties/{property_id}/check", params=params)
    response.raise_for_status()
    data = response.json()

    status = data.get("status", "unknown")
    total = data.get("total_rules_checked", 0)
    passed = data.get("passed_count", 0)
    failed = data.get("failed_count", 0)
    warnings = data.get("warning_count", 0)
    check_id = data.get("id")
    summary = data.get("ai_summary", "")

    text = f"Compliance Check Complete (ID: {check_id})\n\n"
    text += f"Status: {status.upper()}\n"
    text += f"Rules checked: {total} | Passed: {passed} | Failed: {failed} | Warnings: {warnings}\n"

    if summary:
        text += f"\nSummary: {summary}\n"

    violations = data.get("violations", [])
    if violations:
        text += f"\nViolations ({len(violations)}):\n"
        for v in violations[:10]:
            severity = v.get("severity", "")
            message = v.get("violation_message", "")
            text += f"  [{severity.upper()}] {message}\n"
        if len(violations) > 10:
            text += f"  ... and {len(violations) - 10} more\n"

    text += f"\nUse 'get_compliance_report' for the full report or 'resolve_compliance_violation' to resolve issues."

    return [TextContent(type="text", text=text)]


async def handle_get_compliance_history(arguments: dict) -> list[TextContent]:
    """Get compliance check history for a property."""
    property_id = arguments.get("property_id")
    limit = arguments.get("limit", 10)

    if not property_id:
        return [TextContent(type="text", text="Error: property_id is required.")]

    response = api_get(f"/compliance/properties/{property_id}/checks", params={"limit": limit})
    response.raise_for_status()
    checks = response.json()

    if not checks:
        return [TextContent(type="text", text=f"No compliance checks found for property {property_id}. Run a check first.")]

    text = f"Compliance History for Property {property_id} ({len(checks)} checks)\n\n"

    for check in checks:
        check_id = check.get("id")
        status = check.get("status", "unknown")
        check_type = check.get("check_type", "full")
        created = check.get("created_at", "")
        failed = check.get("failed_count", 0)
        warnings = check.get("warning_count", 0)

        text += f"  Check {check_id} ({check_type}) - {status.upper()} - {created}\n"
        text += f"    Failed: {failed} | Warnings: {warnings}\n"

    return [TextContent(type="text", text=text)]


async def handle_get_compliance_report(arguments: dict) -> list[TextContent]:
    """Get a comprehensive compliance report for a property."""
    property_id = arguments.get("property_id")

    if not property_id:
        return [TextContent(type="text", text="Error: property_id is required.")]

    response = api_get(f"/compliance/properties/{property_id}/report")
    response.raise_for_status()
    data = response.json()

    if not data.get("has_been_checked", True) is True and data.get("has_been_checked") is False:
        return [TextContent(type="text", text=f"No compliance check has been run on property {property_id} yet. Run one first with 'run_compliance_check'.")]

    if data.get("has_been_checked") is False:
        return [TextContent(type="text", text=data.get("message", f"No compliance check found for property {property_id}."))]

    address = data.get("property_address", "")
    status = data.get("overall_status", "unknown")
    ready = data.get("is_ready_to_list", False)
    summary = data.get("summary", "")
    stats = data.get("statistics", {})
    fix_cost = data.get("estimated_total_fix_cost", 0)
    fix_time = data.get("estimated_total_fix_time_days", 0)

    text = f"Compliance Report: {address}\n\n"
    text += f"Status: {status.upper()}\n"
    text += f"Ready to list: {'Yes' if ready else 'No'}\n"
    text += f"Rules checked: {stats.get('total_rules_checked', 0)} | Passed: {stats.get('passed', 0)} | Failed: {stats.get('failed', 0)} | Warnings: {stats.get('warnings', 0)}\n"

    if summary:
        text += f"\nSummary: {summary}\n"

    violations_by_severity = data.get("violations_by_severity", {})
    has_violations = any(violations_by_severity.get(s) for s in ["critical", "high", "medium", "low", "info"])

    if has_violations:
        text += "\nOpen Violations:\n"
        for severity in ["critical", "high", "medium", "low", "info"]:
            violations = violations_by_severity.get(severity, [])
            if violations:
                text += f"\n  [{severity.upper()}] ({len(violations)}):\n"
                for v in violations:
                    text += f"    - {v.get('rule_title', '')}: {v.get('message', '')}\n"
                    if v.get("recommendation"):
                        text += f"      Fix: {v['recommendation']}\n"

    if fix_cost > 0:
        text += f"\nEstimated total fix cost: ${fix_cost:,.0f}\n"
    if fix_time > 0:
        text += f"Estimated fix time: {fix_time} days\n"

    return [TextContent(type="text", text=text)]


async def handle_resolve_compliance_violation(arguments: dict) -> list[TextContent]:
    """Resolve a compliance violation."""
    violation_id = arguments.get("violation_id")
    resolution_notes = arguments.get("resolution_notes", "")

    if not violation_id:
        return [TextContent(type="text", text="Error: violation_id is required.")]

    if not resolution_notes:
        return [TextContent(type="text", text="Error: resolution_notes is required. Describe how the violation was resolved.")]

    response = api_post(
        f"/compliance/violations/{violation_id}/resolve",
        params={"resolution_notes": resolution_notes},
    )
    response.raise_for_status()
    data = response.json()

    text = f"Violation {violation_id} resolved.\n"
    text += f"Notes: {data.get('resolution_notes', resolution_notes)}\n"
    text += "\nRun a new compliance check to verify all issues are addressed."

    return [TextContent(type="text", text=text)]


# ── Registration ──

register_tool(
    Tool(
        name="run_compliance_check",
        description=(
            "Run a compliance check on a property to evaluate it against applicable "
            "state and local real estate regulations. Checks disclosures, safety codes, "
            "zoning, and environmental rules. Returns pass/fail status with detailed violations. "
            "Use before listing a property to ensure regulatory compliance. "
            "Supports check types: full, disclosure_only, safety_only, zoning_only, environmental_only."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "ID of the property to check",
                },
                "check_type": {
                    "type": "string",
                    "description": "Type of check to run (default: full)",
                    "enum": ["full", "disclosure_only", "safety_only", "zoning_only", "environmental_only"],
                    "default": "full",
                },
                "agent_id": {
                    "type": "number",
                    "description": "Agent ID running the check (optional)",
                },
            },
            "required": ["property_id"],
        },
    ),
    handle_run_compliance_check,
)

register_tool(
    Tool(
        name="get_compliance_history",
        description=(
            "Get the compliance check history for a property. Shows all past checks "
            "with their status, dates, and pass/fail counts. Useful for tracking "
            "compliance progress over time or verifying that issues were fixed."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "ID of the property",
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum number of checks to return (default: 10)",
                    "default": 10,
                },
            },
            "required": ["property_id"],
        },
    ),
    handle_get_compliance_history,
)

register_tool(
    Tool(
        name="get_compliance_report",
        description=(
            "Get a comprehensive compliance report for a property. Includes the latest "
            "check results, all open violations grouped by severity (critical/high/medium/low), "
            "fix recommendations, estimated costs, and whether the property is ready to list. "
            "Best tool for a full compliance overview before making listing decisions."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "ID of the property",
                },
            },
            "required": ["property_id"],
        },
    ),
    handle_get_compliance_report,
)

register_tool(
    Tool(
        name="resolve_compliance_violation",
        description=(
            "Mark a compliance violation as resolved. Requires a description of how "
            "the issue was fixed. After resolving violations, run a new compliance check "
            "to confirm the property is now compliant."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "violation_id": {
                    "type": "number",
                    "description": "ID of the violation to resolve",
                },
                "resolution_notes": {
                    "type": "string",
                    "description": "Description of how the violation was resolved",
                },
            },
            "required": ["violation_id", "resolution_notes"],
        },
    ),
    handle_resolve_compliance_violation,
)
