"""Transaction Coordinator MCP tools — manage deals from accepted offer to closing."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post, api_put


async def handle_create_transaction(arguments: dict) -> list[TextContent]:
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id.")]

    payload = {"property_id": property_id}
    for key in ("offer_id", "title", "accepted_date", "closing_date", "sale_price",
                "earnest_money", "commission_rate", "financing_type", "notes",
                "attorney_review_deadline", "inspection_deadline",
                "appraisal_deadline", "mortgage_contingency_date"):
        if arguments.get(key) is not None:
            payload[key] = arguments[key]

    if arguments.get("parties"):
        payload["parties"] = arguments["parties"]

    response = api_post("/transactions/", json=payload)
    response.raise_for_status()
    txn = response.json()

    milestones = txn.get("milestones", [])
    text = f"Transaction #{txn['id']} created for property #{txn['property_id']}\n"
    text += f"Status: {txn['status']} | Closing: {txn.get('closing_date', 'TBD')[:10]}\n"
    if txn.get("sale_price"):
        text += f"Sale Price: ${txn['sale_price']:,.0f}\n"
    text += f"\n{len(milestones)} milestones auto-created:\n"
    for m in milestones:
        text += f"  • {m['name']} — due {m.get('due_date', 'TBD')[:10] if m.get('due_date') else 'TBD'}\n"

    return [TextContent(type="text", text=text)]


async def handle_get_transaction(arguments: dict) -> list[TextContent]:
    txn_id = arguments.get("transaction_id")
    if not txn_id:
        return [TextContent(type="text", text="Please provide a transaction_id.")]

    response = api_get(f"/transactions/{txn_id}")
    response.raise_for_status()
    txn = response.json()

    text = f"Transaction #{txn['id']}: {txn['title']}\n"
    text += f"Status: {txn['status']} | Property: #{txn['property_id']}\n"
    if txn.get("sale_price"):
        text += f"Sale Price: ${txn['sale_price']:,.0f}\n"
    if txn.get("closing_date"):
        text += f"Closing Date: {txn['closing_date'][:10]}\n"
    if txn.get("financing_type"):
        text += f"Financing: {txn['financing_type']}\n"

    parties = txn.get("parties", [])
    if parties:
        text += f"\nParties ({len(parties)}):\n"
        for p in parties:
            text += f"  • {p['name']} ({p['role']})"
            if p.get("email"):
                text += f" — {p['email']}"
            text += "\n"

    milestones = txn.get("milestones", [])
    if milestones:
        text += f"\nMilestones ({len(milestones)}):\n"
        for m in milestones:
            icon = "✓" if m["status"] == "completed" else "⚠" if m["status"] == "overdue" else "○"
            text += f"  {icon} {m['name']} [{m['status']}]"
            if m.get("due_date"):
                text += f" — due {m['due_date'][:10]}"
            if m.get("assigned_name"):
                text += f" ({m['assigned_name']})"
            text += "\n"

    risk_flags = txn.get("risk_flags", [])
    if risk_flags:
        text += f"\nRisk Flags: {', '.join(risk_flags)}\n"

    return [TextContent(type="text", text=text)]


async def handle_list_transactions(arguments: dict) -> list[TextContent]:
    params = {}
    if arguments.get("status"):
        params["status"] = arguments["status"]
    if arguments.get("property_id"):
        params["property_id"] = arguments["property_id"]

    response = api_get("/transactions/", params=params)
    response.raise_for_status()
    txns = response.json()

    if not txns:
        return [TextContent(type="text", text="No transactions found.")]

    text = f"Transactions ({len(txns)}):\n\n"
    for t in txns:
        text += f"  #{t['id']} — {t['title']} [{t['status']}]"
        if t.get("closing_date"):
            text += f" | Close: {t['closing_date'][:10]}"
        if t.get("sale_price"):
            text += f" | ${t['sale_price']:,.0f}"
        text += "\n"

    return [TextContent(type="text", text=text)]


async def handle_update_milestone(arguments: dict) -> list[TextContent]:
    milestone_id = arguments.get("milestone_id")
    if not milestone_id:
        return [TextContent(type="text", text="Please provide a milestone_id.")]

    payload = {}
    for key in ("status", "outcome_notes", "completed_at", "due_date", "assigned_name", "assigned_contact"):
        if arguments.get(key) is not None:
            payload[key] = arguments[key]

    response = api_put(f"/transactions/milestones/{milestone_id}", json=payload)
    response.raise_for_status()
    m = response.json()

    text = f"Milestone #{m['id']} updated: {m['name']} → {m['status']}"
    if m.get("completed_at"):
        text += f" (completed {m['completed_at'][:10]})"
    if m.get("outcome_notes"):
        text += f"\nNotes: {m['outcome_notes']}"

    return [TextContent(type="text", text=text)]


async def handle_check_deadlines(arguments: dict) -> list[TextContent]:
    response = api_get("/transactions/check-deadlines")
    response.raise_for_status()
    data = response.json()

    alerts = data.get("alerts", [])
    if not alerts:
        return [TextContent(type="text", text="All transaction milestones are on track. No overdue or upcoming deadlines.")]

    text = f"Transaction Deadline Alerts ({len(alerts)}):\n\n"
    for a in alerts:
        icon = "🔴" if a["type"] == "overdue" else "🟡"
        text += f"{icon} {a['message']}\n"
        if a.get("assigned_role"):
            text += f"   Responsible: {a['assigned_role']}\n"
    return [TextContent(type="text", text=text)]


async def handle_transaction_pipeline(arguments: dict) -> list[TextContent]:
    response = api_get("/transactions/pipeline")
    response.raise_for_status()
    data = response.json()

    text = f"Transaction Pipeline:\n"
    text += f"Active: {data['active_count']} | Total Value: ${data['total_pipeline_value']:,.0f}\n\n"

    text += "By Status:\n"
    for status, count in data.get("by_status", {}).items():
        text += f"  {status}: {count}\n"

    upcoming = data.get("upcoming_7_days", [])
    if upcoming:
        text += f"\nUpcoming This Week ({len(upcoming)}):\n"
        for u in upcoming:
            text += f"  • {u['milestone']} — {u['title']} (due {u['due_date'][:10]}) [{u['status']}]\n"

    return [TextContent(type="text", text=text)]


async def handle_transaction_summary(arguments: dict) -> list[TextContent]:
    txn_id = arguments.get("transaction_id")
    if not txn_id:
        return [TextContent(type="text", text="Please provide a transaction_id.")]

    response = api_get(f"/transactions/{txn_id}/summary")
    response.raise_for_status()
    s = response.json()

    text = f"Transaction #{s['id']} Summary: {s['title']}\n"
    text += f"Status: {s['status']}\n"
    if s.get("sale_price"):
        text += f"Sale Price: ${s['sale_price']:,.0f}\n"
    if s.get("days_to_close") is not None:
        text += f"Days to Close: {s['days_to_close']}\n"
    text += f"Milestones: {s['milestones_completed']}/{s['milestones_total']} completed\n"
    if s.get("overdue_milestones"):
        text += f"⚠ Overdue: {s['overdue_milestones']}\n"
    if s.get("risk_flags"):
        text += f"Risk Flags: {', '.join(s['risk_flags'])}\n"

    return [TextContent(type="text", text=text)]


async def handle_add_party(arguments: dict) -> list[TextContent]:
    txn_id = arguments.get("transaction_id")
    name = arguments.get("name")
    role = arguments.get("role")
    if not txn_id or not name or not role:
        return [TextContent(type="text", text="Please provide transaction_id, name, and role.")]

    params = {"name": name, "role": role}
    if arguments.get("email"):
        params["email"] = arguments["email"]
    if arguments.get("phone"):
        params["phone"] = arguments["phone"]

    response = api_post(f"/transactions/{txn_id}/party", params=params)
    response.raise_for_status()
    data = response.json()

    parties = data.get("parties", [])
    text = f"Party added. Transaction now has {len(parties)} parties:\n"
    for p in parties:
        text += f"  • {p['name']} ({p['role']})\n"
    return [TextContent(type="text", text=text)]


async def handle_check_deadlines_notify(arguments: dict) -> list[TextContent]:
    response = api_post("/transactions/check-deadlines/notify")
    response.raise_for_status()
    data = response.json()

    if data.get("alerts", 0) == 0:
        return [TextContent(type="text", text="All transaction milestones are on track. No alerts generated.")]

    text = f"Deadline Check Complete:\n"
    text += f"  Overdue: {data.get('overdue', 0)}\n"
    text += f"  Upcoming: {data.get('upcoming', 0)}\n"
    text += f"  Notifications Created: {data.get('notifications_created', 0)}\n"

    details = data.get("details", [])
    if details:
        text += f"\nAlerts:\n"
        for a in details[:10]:
            icon = "🔴" if a["type"] == "overdue" else "🟡"
            text += f"  {icon} {a['message']}\n"

    return [TextContent(type="text", text=text)]


async def handle_add_risk_flag(arguments: dict) -> list[TextContent]:
    txn_id = arguments.get("transaction_id")
    flag = arguments.get("flag")
    if not txn_id or not flag:
        return [TextContent(type="text", text="Please provide transaction_id and flag.")]

    response = api_post(f"/transactions/{txn_id}/risk-flag", params={"flag": flag})
    response.raise_for_status()
    data = response.json()
    return [TextContent(type="text", text=f"Risk flags: {', '.join(data.get('risk_flags', []))}")]


# ── Tool Registration ──

register_tool(Tool(
    name="create_transaction",
    description="Start a new transaction to track a deal from accepted offer to closing. Auto-creates 9 milestone checkpoints (attorney review, inspection, appraisal, mortgage commitment, title search, final walkthrough, closing). Voice: 'Start tracking the deal on 123 Main St' or 'Create transaction for property 5, closing May 15'.",
    inputSchema={
        "type": "object",
        "properties": {
            "property_id": {"type": "number", "description": "Property ID"},
            "offer_id": {"type": "number", "description": "Accepted offer ID (optional)"},
            "title": {"type": "string", "description": "Transaction title (auto-generated if omitted)"},
            "accepted_date": {"type": "string", "description": "Offer accepted date (ISO format, defaults to now)"},
            "closing_date": {"type": "string", "description": "Target closing date (ISO format, defaults to +45 days)"},
            "sale_price": {"type": "number", "description": "Sale price"},
            "earnest_money": {"type": "number", "description": "Earnest money deposit"},
            "commission_rate": {"type": "number", "description": "Commission rate (e.g. 0.03 for 3%)"},
            "financing_type": {"type": "string", "description": "Financing: cash, conventional, FHA, VA"},
            "parties": {"type": "array", "description": "List of parties: [{name, role, email, phone}]", "items": {"type": "object"}},
            "notes": {"type": "string", "description": "Additional notes"},
        },
        "required": ["property_id"],
    },
), handle_create_transaction)

register_tool(Tool(
    name="get_transaction",
    description="Get full details of a transaction including all milestones, parties, and risk flags. Voice: 'Show me transaction 3' or 'What's the status of the Main St deal?'.",
    inputSchema={
        "type": "object",
        "properties": {
            "transaction_id": {"type": "number", "description": "Transaction ID"},
        },
        "required": ["transaction_id"],
    },
), handle_get_transaction)

register_tool(Tool(
    name="list_transactions",
    description="List all transactions, optionally filtered by status or property. Voice: 'Show all active transactions' or 'List closed deals'.",
    inputSchema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Filter: initiated, attorney_review, inspections, appraisal, mortgage_contingency, title_search, final_walkthrough, closing_scheduled, closed, fell_through, cancelled"},
            "property_id": {"type": "number", "description": "Filter by property"},
        },
    },
), handle_list_transactions)

register_tool(Tool(
    name="update_transaction_milestone",
    description="Update a transaction milestone — mark completed, add notes, change due date. Auto-advances transaction status when milestones complete. Voice: 'Mark inspection as completed' or 'Appraisal came in, no issues'.",
    inputSchema={
        "type": "object",
        "properties": {
            "milestone_id": {"type": "number", "description": "Milestone ID"},
            "status": {"type": "string", "description": "New status: pending, in_progress, completed, overdue, waived, failed"},
            "outcome_notes": {"type": "string", "description": "What happened — inspection results, appraisal value, etc."},
            "due_date": {"type": "string", "description": "New due date (ISO format)"},
            "assigned_name": {"type": "string", "description": "Name of person responsible"},
            "assigned_contact": {"type": "string", "description": "Email or phone of assignee"},
        },
        "required": ["milestone_id"],
    },
), handle_update_milestone)

register_tool(Tool(
    name="check_transaction_deadlines",
    description="Scan all active transactions for overdue or upcoming milestones. Returns alerts for anything due within 24 hours or past due. Voice: 'Any deadlines coming up?' or 'Check on my transactions'.",
    inputSchema={"type": "object", "properties": {}},
), handle_check_deadlines)

register_tool(Tool(
    name="get_transaction_pipeline",
    description="Overview of all active transactions — counts by status, total pipeline value, upcoming milestones this week. Voice: 'Show my deal pipeline' or 'How many deals are in progress?'.",
    inputSchema={"type": "object", "properties": {}},
), handle_transaction_pipeline)

register_tool(Tool(
    name="get_transaction_summary",
    description="Quick summary of a transaction — milestone progress, days to close, risk flags. Voice: 'Give me a summary of transaction 5'.",
    inputSchema={
        "type": "object",
        "properties": {
            "transaction_id": {"type": "number", "description": "Transaction ID"},
        },
        "required": ["transaction_id"],
    },
), handle_transaction_summary)

register_tool(Tool(
    name="add_transaction_party",
    description="Add a party (buyer, seller, attorney, lender, inspector, etc.) to a transaction. Voice: 'Add John Smith as the buyer's attorney on transaction 3'.",
    inputSchema={
        "type": "object",
        "properties": {
            "transaction_id": {"type": "number", "description": "Transaction ID"},
            "name": {"type": "string", "description": "Person's name"},
            "role": {"type": "string", "description": "Role: buyer, seller, buyer_agent, seller_agent, attorney, lender, title_company, inspector, appraiser"},
            "email": {"type": "string", "description": "Email address"},
            "phone": {"type": "string", "description": "Phone number"},
        },
        "required": ["transaction_id", "name", "role"],
    },
), handle_add_party)

register_tool(Tool(
    name="add_transaction_risk_flag",
    description="Flag a risk on a transaction — appraisal gap, slow lender, title issue, etc. Voice: 'Flag that the lender is slow on transaction 3'.",
    inputSchema={
        "type": "object",
        "properties": {
            "transaction_id": {"type": "number", "description": "Transaction ID"},
            "flag": {"type": "string", "description": "Risk flag: appraisal_gap_risk, slow_lender, title_issue, inspection_concerns, financing_risk, seller_contingency, etc."},
        },
        "required": ["transaction_id", "flag"],
    },
), handle_add_risk_flag)

register_tool(Tool(
    name="trigger_transaction_deadline_check",
    description="Run the full transaction deadline check with notifications. Scans all active deals, flags overdue milestones, creates notifications, and optionally sends SMS alerts. Same as the automated cron job but triggered manually. Voice: 'Run deadline check on all my deals' or 'Check all transaction deadlines and notify me'.",
    inputSchema={"type": "object", "properties": {}},
), handle_check_deadlines_notify)
