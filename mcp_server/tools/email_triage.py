"""
Email Triage MCP Tools — check emails, classify, draft replies, get digest.
"""
import httpx
from mcp.types import Tool, TextContent
from ..server import register_tool
from ..utils.http_client import API_BASE_URL
from typing import Dict, Any, List


# ==========================================================================
# CHECK EMAILS
# ==========================================================================

async def handle_check_emails(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Trigger email check and triage.

    Voice: "Check my emails"
    Voice: "Triage my inbox"
    """
    since_minutes = arguments.get("since_minutes", 30)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/email/triage/check",
            json={"since_minutes": since_minutes},
            timeout=60.0,
        )
        response.raise_for_status()
        result = response.json()

    processed = result.get("emails_processed", 0)
    summary = result.get("summary", {})

    if processed == 0:
        return [TextContent(type="text", text="No new emails found in the last {} minutes.".format(since_minutes))]

    lines = [f"Processed {processed} email(s):"]
    for cat, count in summary.items():
        lines.append(f"  - {cat.replace('_', ' ').title()}: {count}")

    return [TextContent(type="text", text="\n".join(lines))]


# ==========================================================================
# GET EMAIL DIGEST
# ==========================================================================

async def handle_get_email_digest(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Get summary of recent emails by category.

    Voice: "Give me an email summary"
    Voice: "What's in my inbox today?"
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/email/triage/digest",
            timeout=30.0,
        )
        response.raise_for_status()
        result = response.json()

    digest = result.get("digest", "No emails processed yet.")
    total = result.get("total_processed", 0)

    # Strip HTML tags for voice output
    import re
    clean = re.sub(r"<[^>]+>", "", digest)

    return [TextContent(type="text", text=f"Email digest ({total} emails):\n\n{clean}")]


# ==========================================================================
# CLASSIFY EMAIL
# ==========================================================================

async def handle_classify_email(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Classify an email's urgency and category.

    Voice: "Classify this email"
    """
    subject = arguments.get("subject", "")
    body = arguments.get("body", "")
    from_address = arguments.get("from_address", "")
    from_name = arguments.get("from_name", "")

    if not subject and not body:
        return [TextContent(type="text", text="Please provide at least a subject or body to classify.")]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/email/triage/classify",
            json={
                "subject": subject,
                "body": body,
                "from_address": from_address,
                "from_name": from_name,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        result = response.json()

    classification = result.get("classification", "general")
    priority = result.get("priority", 4)
    reasoning = result.get("reasoning", "")

    lines = [
        f"Classification: {classification.replace('_', ' ').title()}",
        f"Priority: {priority}/5",
        f"Reasoning: {reasoning}",
    ]
    key_details = result.get("key_details", "")
    if key_details:
        lines.append(f"Key Details: {key_details}")

    return [TextContent(type="text", text="\n".join(lines))]


# ==========================================================================
# DRAFT EMAIL REPLY
# ==========================================================================

async def handle_draft_email_reply(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Draft a reply to a specific email.

    Voice: "Draft a reply to this email"
    """
    subject = arguments.get("subject", "")
    body = arguments.get("body", "")
    from_address = arguments.get("from_address", "")
    from_name = arguments.get("from_name", "")
    classification = arguments.get("classification", "warm_lead")

    if not subject and not body:
        return [TextContent(type="text", text="Please provide at least a subject or body to draft a reply.")]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/email/triage/draft-reply",
            json={
                "subject": subject,
                "body": body,
                "from_address": from_address,
                "from_name": from_name,
                "classification": classification,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        result = response.json()

    draft = result.get("drafted_response", "")
    if not draft:
        return [TextContent(type="text", text="Could not generate a draft reply.")]

    return [TextContent(type="text", text=f"Draft Reply ({classification.replace('_', ' ').title()}):\n\n{draft}")]


# ==========================================================================
# REGISTER TOOLS
# ==========================================================================

register_tool(
    Tool(
        name="check_emails",
        description="Trigger email check and triage. Fetches recent unread emails, classifies them, drafts replies for leads, and sends Telegram alerts. Voice: 'Check my emails' or 'Triage my inbox'.",
        inputSchema={
            "type": "object",
            "properties": {
                "since_minutes": {
                    "type": "integer",
                    "description": "How far back to check in minutes (default 30, max 1440)",
                    "default": 30,
                },
            },
        },
    ),
    handle_check_emails,
)

register_tool(
    Tool(
        name="get_email_digest",
        description="Get summary of recent emails grouped by category (hot leads, warm leads, showing requests, etc). Voice: 'Give me an email summary' or 'What's in my inbox today?'.",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_get_email_digest,
)

register_tool(
    Tool(
        name="classify_email",
        description="Classify an email's urgency and category (hot_lead, warm_lead, contract_update, showing_request, spam, general). Voice: 'Classify this email'.",
        inputSchema={
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "Email subject line",
                },
                "body": {
                    "type": "string",
                    "description": "Email body text",
                },
                "from_address": {
                    "type": "string",
                    "description": "Sender email address",
                },
                "from_name": {
                    "type": "string",
                    "description": "Sender name",
                },
            },
            "required": ["subject", "body"],
        },
    ),
    handle_classify_email,
)

register_tool(
    Tool(
        name="draft_email_reply",
        description="Draft a professional reply to an email. Voice: 'Draft a reply to this email'.",
        inputSchema={
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "Email subject line",
                },
                "body": {
                    "type": "string",
                    "description": "Email body text",
                },
                "from_address": {
                    "type": "string",
                    "description": "Sender email address",
                },
                "from_name": {
                    "type": "string",
                    "description": "Sender name",
                },
                "classification": {
                    "type": "string",
                    "description": "Email classification (hot_lead, warm_lead, etc)",
                    "default": "warm_lead",
                },
            },
            "required": ["subject", "body"],
        },
    ),
    handle_draft_email_reply,
)
