"""Deal Journal MCP tools — log and search every deal interaction."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_log_journal(arguments: dict) -> list[TextContent]:
    title = arguments.get("title")
    content = arguments.get("content")
    if not title or not content:
        return [TextContent(type="text", text="Please provide both title and content.")]

    payload = {
        "entry_type": arguments.get("entry_type", "note"),
        "title": title,
        "content": content,
    }
    for key in ("property_id", "contact_id", "participants", "outcome", "follow_up", "tags"):
        if arguments.get(key):
            payload[key] = arguments[key]

    response = api_post("/journal/log", json=payload)
    response.raise_for_status()
    data = response.json()
    return [TextContent(type="text", text=f"Logged to deal journal (ID: {data['id']}). Auto-ingested to knowledge base for future RAG search.")]


async def handle_search_journal(arguments: dict) -> list[TextContent]:
    query = arguments.get("query")
    if not query:
        return [TextContent(type="text", text="Please provide a search query.")]

    payload = {"query": query, "limit": arguments.get("limit", 10)}
    if arguments.get("property_id"):
        payload["property_id"] = arguments["property_id"]

    response = api_post("/journal/search", json=payload)
    response.raise_for_status()
    data = response.json()

    results = data.get("results", [])
    if not results:
        return [TextContent(type="text", text=f"No journal entries found for: {query}")]

    text = f"Deal Journal — {len(results)} results for: {query}\n\n"
    for i, r in enumerate(results, 1):
        text += f"{i}. [{r.get('type', '?').upper()}] {r['title']}\n"
        if r.get("outcome"):
            text += f"   Outcome: {r['outcome']}\n"
        if r.get("content_preview"):
            text += f"   {r['content_preview'][:200]}\n"
        if r.get("created_at"):
            text += f"   Date: {r['created_at'][:10]}\n"
        if r.get("similarity"):
            text += f"   Relevance: {r['similarity']:.0%}\n"
        text += "\n"

    return [TextContent(type="text", text=text)]


async def handle_property_journal(arguments: dict) -> list[TextContent]:
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id.")]

    response = api_get(f"/journal/property/{property_id}")
    response.raise_for_status()
    data = response.json()

    entries = data.get("entries", [])
    if not entries:
        return [TextContent(type="text", text=f"No journal entries for property {property_id}.")]

    text = f"Deal Journal — Property #{property_id} ({len(entries)} entries):\n\n"
    for e in entries:
        text += f"  [{e.get('type', '?').upper()}] {e['title']}"
        if e.get("created_at"):
            text += f" ({e['created_at'][:10]})"
        text += "\n"
        if e.get("outcome"):
            text += f"    Outcome: {e['outcome']}\n"
        if e.get("follow_up"):
            text += f"    Follow-up: {e['follow_up']}\n"

    return [TextContent(type="text", text=text)]


async def handle_recent_journal(arguments: dict) -> list[TextContent]:
    params = {}
    if arguments.get("entry_type"):
        params["entry_type"] = arguments["entry_type"]

    response = api_get("/journal/recent", params=params)
    response.raise_for_status()
    data = response.json()

    entries = data.get("entries", [])
    if not entries:
        return [TextContent(type="text", text="No recent journal entries.")]

    text = f"Recent Journal Entries ({len(entries)}):\n\n"
    for e in entries:
        text += f"  [{e.get('type', '?').upper()}] {e['title']}"
        if e.get("created_at"):
            text += f" ({e['created_at'][:10]})"
        text += "\n"

    return [TextContent(type="text", text=text)]


# ── Tool Registration ──

register_tool(Tool(
    name="log_deal_journal",
    description="Log an interaction to the deal journal. Every call, email, showing, meeting, offer, or note gets recorded and auto-ingested into the knowledge base for future RAG search. Voice: 'Log that the seller said the roof was replaced in 2020' or 'Journal entry: showed property to the Johnsons, they loved the kitchen'.",
    inputSchema={
        "type": "object",
        "properties": {
            "entry_type": {"type": "string", "description": "Type: call, email, showing, meeting, offer, negotiation, inspection, appraisal, closing, note"},
            "title": {"type": "string", "description": "Brief title of the interaction"},
            "content": {"type": "string", "description": "Full details of what happened, what was discussed, any commitments made"},
            "property_id": {"type": "number", "description": "Property ID if related to a specific property"},
            "contact_id": {"type": "number", "description": "Contact ID if related to a specific person"},
            "participants": {"type": "string", "description": "Who was involved (names)"},
            "outcome": {"type": "string", "description": "What was decided or agreed"},
            "follow_up": {"type": "string", "description": "Next steps or action items"},
            "tags": {"type": "string", "description": "Comma-separated tags (e.g. 'roof,inspection,repair')"},
        },
        "required": ["title", "content"],
    },
), handle_log_journal)

register_tool(Tool(
    name="search_deal_journal",
    description="Search the deal journal using keywords + semantic RAG search. Find past conversations, decisions, and interactions. Voice: 'What did the seller say about the roof?' or 'Find all interactions with the Johnson family'.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "property_id": {"type": "number", "description": "Filter by property ID"},
            "limit": {"type": "number", "description": "Max results", "default": 10},
        },
        "required": ["query"],
    },
), handle_search_journal)

register_tool(Tool(
    name="get_property_journal",
    description="Get the complete interaction history for a property. Voice: 'Show me all journal entries for 123 Main St'.",
    inputSchema={
        "type": "object",
        "properties": {
            "property_id": {"type": "number", "description": "Property ID"},
        },
        "required": ["property_id"],
    },
), handle_property_journal)

register_tool(Tool(
    name="get_recent_journal",
    description="Get recent deal journal entries. Voice: 'Show me recent journal entries' or 'What calls did we log recently?'.",
    inputSchema={
        "type": "object",
        "properties": {
            "entry_type": {"type": "string", "description": "Filter by type: call, email, showing, meeting, offer, note"},
        },
    },
), handle_recent_journal)
