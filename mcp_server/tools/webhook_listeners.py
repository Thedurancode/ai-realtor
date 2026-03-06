"""Webhook Listener MCP tools — register, list, and test webhook listeners."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


# ── Handlers ─────────────────────────────────────────────────────────────

async def handle_register_webhook(arguments: dict) -> list[TextContent]:
    """Register a new webhook listener."""
    url = arguments.get("url")
    event_type = arguments.get("event_type")

    if not url or not event_type:
        return [TextContent(type="text", text="Please provide both a 'url' and an 'event_type'.")]

    body = {
        "url": url,
        "event_type": event_type,
    }
    if arguments.get("secret"):
        body["secret"] = arguments["secret"]

    response = api_post("/webhooks/listeners/register", json=body)
    response.raise_for_status()
    data = response.json()

    text = (
        f"Webhook registered (ID #{data['id']}).\n"
        f"URL: {data['url']}\n"
        f"Event type: {data['event_type']}\n"
        f"Active: {data['is_active']}"
    )
    return [TextContent(type="text", text=text)]


async def handle_list_webhooks(arguments: dict) -> list[TextContent]:
    """List all registered webhooks."""
    params = {}
    if arguments.get("event_type"):
        params["event_type"] = arguments["event_type"]

    response = api_get("/webhooks/listeners/registered", params=params)
    response.raise_for_status()
    data = response.json()

    if not data:
        return [TextContent(type="text", text="No webhooks registered yet. Use 'register_webhook' to add one.")]

    text = f"REGISTERED WEBHOOKS ({len(data)})\n{'=' * 40}\n\n"
    for wh in data:
        secret_status = "yes" if wh.get("has_secret") else "no"
        active_status = "ACTIVE" if wh.get("is_active") else "INACTIVE"
        text += (
            f"#{wh['id']} [{active_status}] {wh['event_type']}\n"
            f"  URL: {wh['url']}\n"
            f"  Secret: {secret_status}\n"
            f"  Created: {wh.get('created_at', 'N/A')}\n\n"
        )
    return [TextContent(type="text", text=text)]


async def handle_test_webhook(arguments: dict) -> list[TextContent]:
    """Send a test webhook event."""
    event_type = arguments.get("event_type")
    if not event_type:
        return [TextContent(type="text", text="Please provide an 'event_type' to test.")]

    body = {}
    if arguments.get("payload"):
        body["payload"] = arguments["payload"]

    response = api_post(f"/webhooks/listeners/test/{event_type}", json=body)
    response.raise_for_status()
    data = response.json()

    result = data.get("result", {})
    actions = result.get("actions", [])
    actions_str = ", ".join(actions) if actions else "none"

    text = (
        f"Test webhook fired: {event_type}\n"
        f"Actions taken: {actions_str}\n"
    )
    if result.get("error"):
        text += f"Error: {result['error']}\n"
    if result.get("score"):
        text += f"Score: {result['score']}\n"
    if result.get("recommendation"):
        text += f"Recommendation: {result['recommendation']}\n"

    return [TextContent(type="text", text=text)]


# ── Tool Registration ────────────────────────────────────────────────────

register_tool(
    Tool(
        name="register_webhook",
        description=(
            "Register a new webhook listener to receive real-time events. "
            "Event types: new_lead, property_update, offer_received, contract_signed, "
            "email_received, mls_listing. "
            "Voice: 'Register a webhook for new leads', 'Set up a webhook for offer notifications'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to receive webhook POST requests"},
                "event_type": {
                    "type": "string",
                    "description": "Event type to listen for",
                    "enum": [
                        "new_lead",
                        "property_update",
                        "offer_received",
                        "contract_signed",
                        "email_received",
                        "mls_listing",
                    ],
                },
                "secret": {
                    "type": "string",
                    "description": "Optional shared secret for webhook signature verification",
                },
            },
            "required": ["url", "event_type"],
        },
    ),
    handle_register_webhook,
)

register_tool(
    Tool(
        name="list_webhooks",
        description=(
            "List all registered webhook listeners. "
            "Voice: 'Show my webhooks', 'List registered webhooks', 'What webhooks do I have?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Filter by event type (optional)",
                },
            },
        },
    ),
    handle_list_webhooks,
)

register_tool(
    Tool(
        name="test_webhook",
        description=(
            "Send a test webhook event to exercise the processing pipeline. "
            "Uses sample data if no custom payload is provided. "
            "Voice: 'Test the new_lead webhook', 'Send a test offer_received event'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Event type to test",
                    "enum": [
                        "new_lead",
                        "property_update",
                        "offer_received",
                        "contract_signed",
                        "email_received",
                        "mls_listing",
                    ],
                },
                "payload": {
                    "type": "object",
                    "description": "Custom payload (optional — sample data used if omitted)",
                },
            },
            "required": ["event_type"],
        },
    ),
    handle_test_webhook,
)
