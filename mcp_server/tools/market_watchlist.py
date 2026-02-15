"""Market Watchlist MCP tools — saved-search alerts for matching properties."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post, api_put, api_delete


async def handle_create_watchlist(arguments: dict) -> list[TextContent]:
    """Create a new market watchlist."""
    name = arguments.get("name")
    if not name:
        return [TextContent(type="text", text="Please provide a watchlist name.")]

    criteria = arguments.get("criteria", {})
    if not criteria:
        return [TextContent(type="text", text="Please provide search criteria (city, max_price, min_bedrooms, etc.).")]

    body = {
        "agent_id": arguments.get("agent_id", 1),
        "name": name,
        "criteria": criteria,
    }
    if arguments.get("description"):
        body["description"] = arguments["description"]

    response = api_post("/watchlists/", json=body)
    response.raise_for_status()
    data = response.json()

    # Build readable criteria summary
    parts = []
    if criteria.get("city"):
        parts.append(f"in {criteria['city']}")
    if criteria.get("state"):
        parts.append(f"state {criteria['state']}")
    if criteria.get("property_type"):
        parts.append(criteria["property_type"])
    if criteria.get("max_price"):
        parts.append(f"under ${criteria['max_price']:,.0f}")
    if criteria.get("min_price"):
        parts.append(f"above ${criteria['min_price']:,.0f}")
    if criteria.get("min_bedrooms"):
        parts.append(f"{criteria['min_bedrooms']}+ beds")
    if criteria.get("min_bathrooms"):
        parts.append(f"{criteria['min_bathrooms']}+ baths")
    if criteria.get("min_sqft"):
        parts.append(f"{criteria['min_sqft']}+ sqft")

    criteria_str = ", ".join(parts) if parts else "custom criteria"

    text = (
        f"Watchlist \"{data['name']}\" created (ID #{data['id']}).\n"
        f"Watching for: {criteria_str}.\n"
        f"You'll be notified when new matching properties are added."
    )
    return [TextContent(type="text", text=text)]


async def handle_list_watchlists(arguments: dict) -> list[TextContent]:
    """List all watchlists."""
    params: dict = {}
    if arguments.get("agent_id"):
        params["agent_id"] = arguments["agent_id"]
    if arguments.get("is_active") is not None:
        params["is_active"] = arguments["is_active"]

    response = api_get("/watchlists/", params=params)
    response.raise_for_status()
    data = response.json()

    if not data:
        return [TextContent(type="text", text="No watchlists found. Create one with 'Watch for Miami condos under 500k'.")]

    text = f"MARKET WATCHLISTS ({len(data)})\n{'=' * 40}\n\n"
    for wl in data:
        status = "ACTIVE" if wl["is_active"] else "PAUSED"
        criteria = wl.get("criteria", {})

        parts = []
        if criteria.get("city"):
            parts.append(criteria["city"])
        if criteria.get("property_type"):
            parts.append(criteria["property_type"])
        if criteria.get("max_price"):
            parts.append(f"<${criteria['max_price']:,.0f}")
        if criteria.get("min_bedrooms"):
            parts.append(f"{criteria['min_bedrooms']}+ beds")

        criteria_str = ", ".join(parts) if parts else "custom"

        text += (
            f"#{wl['id']} {wl['name']} [{status}]\n"
            f"  Criteria: {criteria_str}\n"
            f"  Matches: {wl.get('match_count', 0)}\n\n"
        )

    return [TextContent(type="text", text=text.strip())]


async def handle_toggle_watchlist(arguments: dict) -> list[TextContent]:
    """Toggle a watchlist on/off."""
    watchlist_id = arguments.get("watchlist_id")
    if not watchlist_id:
        return [TextContent(type="text", text="Please provide a watchlist_id.")]

    response = api_post(f"/watchlists/{watchlist_id}/toggle")
    response.raise_for_status()
    data = response.json()

    status = "activated" if data["is_active"] else "paused"
    return [TextContent(type="text", text=f"Watchlist \"{data['name']}\" has been {status}.")]


async def handle_delete_watchlist(arguments: dict) -> list[TextContent]:
    """Delete a watchlist."""
    watchlist_id = arguments.get("watchlist_id")
    if not watchlist_id:
        return [TextContent(type="text", text="Please provide a watchlist_id.")]

    response = api_delete(f"/watchlists/{watchlist_id}")
    response.raise_for_status()

    return [TextContent(type="text", text=f"Watchlist #{watchlist_id} has been deleted.")]


async def handle_check_watchlist_matches(arguments: dict) -> list[TextContent]:
    """Check a property against all active watchlists."""
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id.")]

    response = api_post(f"/watchlists/check/{property_id}")
    response.raise_for_status()
    data = response.json()

    matches = data.get("matches", [])
    addr = data.get("address", f"Property #{property_id}")

    if not matches:
        text = f"{addr} doesn't match any active watchlists ({data.get('total_watchlists_checked', 0)} checked)."
    else:
        text = f"{addr} matches {len(matches)} watchlist(s):\n\n"
        for m in matches:
            text += f"  - #{m['id']} {m['name']}\n"

    return [TextContent(type="text", text=text.strip())]


# ── Registration ──

register_tool(
    Tool(
        name="create_watchlist",
        description=(
            "Create a market watchlist to get alerts when new matching properties are added. "
            "Criteria: city, state, property_type, min_price, max_price, min_bedrooms, min_bathrooms, min_sqft. "
            "Voice: 'Watch for Miami condos under 500k', 'Set up alerts for Brooklyn 3-bedrooms', "
            "'Alert me when houses under 300k in Austin come up'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Watchlist name (e.g., 'Miami Condos Under 500k')"},
                "criteria": {
                    "type": "object",
                    "description": "Search criteria (all AND logic)",
                    "properties": {
                        "city": {"type": "string", "description": "City name (partial match)"},
                        "state": {"type": "string", "description": "State code (e.g., FL, NY)"},
                        "property_type": {
                            "type": "string",
                            "enum": ["house", "condo", "townhouse", "apartment", "land", "commercial", "multi_family"],
                        },
                        "min_price": {"type": "number", "description": "Minimum price"},
                        "max_price": {"type": "number", "description": "Maximum price"},
                        "min_bedrooms": {"type": "number", "description": "Minimum bedrooms"},
                        "min_bathrooms": {"type": "number", "description": "Minimum bathrooms"},
                        "min_sqft": {"type": "number", "description": "Minimum square footage"},
                    },
                },
                "description": {"type": "string", "description": "Optional description"},
                "agent_id": {"type": "number", "description": "Agent ID (default 1)", "default": 1},
            },
            "required": ["name", "criteria"],
        },
    ),
    handle_create_watchlist,
)

register_tool(
    Tool(
        name="list_watchlists",
        description=(
            "List all market watchlists. "
            "Voice: 'Show me my watchlists', 'What am I watching?', 'List my alerts'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "number", "description": "Filter by agent ID"},
                "is_active": {"type": "boolean", "description": "Filter by active/inactive"},
            },
        },
    ),
    handle_list_watchlists,
)

register_tool(
    Tool(
        name="toggle_watchlist",
        description=(
            "Pause or resume a market watchlist. "
            "Voice: 'Pause watchlist 1', 'Turn off watchlist 2', 'Resume watchlist 3'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "watchlist_id": {"type": "number", "description": "The watchlist ID to toggle"},
            },
            "required": ["watchlist_id"],
        },
    ),
    handle_toggle_watchlist,
)

register_tool(
    Tool(
        name="delete_watchlist",
        description=(
            "Delete a market watchlist permanently. "
            "Voice: 'Delete watchlist 3', 'Remove watchlist 1'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "watchlist_id": {"type": "number", "description": "The watchlist ID to delete"},
            },
            "required": ["watchlist_id"],
        },
    ),
    handle_delete_watchlist,
)

register_tool(
    Tool(
        name="check_watchlist_matches",
        description=(
            "Check a property against all active watchlists to see if it matches. "
            "Voice: 'Check property 5 against my watchlists', 'Does property 3 match any watchlists?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "number", "description": "The property ID to check"},
            },
            "required": ["property_id"],
        },
    ),
    handle_check_watchlist_matches,
)
