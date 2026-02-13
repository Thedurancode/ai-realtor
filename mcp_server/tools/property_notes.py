"""Property notes MCP tools for voice-first note-taking."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_add_property_note(arguments: dict) -> list[TextContent]:
    """Add a freeform note to a property via voice."""
    payload = {
        "property_id": arguments["property_id"],
        "content": arguments["content"],
        "source": arguments.get("source", "voice"),
        "created_by": arguments.get("created_by", "voice assistant"),
    }
    response = api_post("/property-notes/", json=payload)
    response.raise_for_status()
    note = response.json()

    return [TextContent(
        type="text",
        text=f"Note added to property #{note['property_id']} (note #{note['id']}): {note['content'][:120]}",
    )]


async def handle_list_property_notes(arguments: dict) -> list[TextContent]:
    """List notes for a property."""
    property_id = arguments["property_id"]
    limit = arguments.get("limit", 10)

    response = api_get(f"/property-notes/property/{property_id}", params={"limit": limit})
    response.raise_for_status()
    result = response.json()

    notes = result.get("notes", [])
    if not notes:
        return [TextContent(type="text", text=f"No notes for property #{property_id}.")]

    text = f"{len(notes)} note(s) for property #{property_id}:\n\n"
    for n in notes:
        source_tag = f" [{n['source']}]" if n.get("source") != "voice" else ""
        text += f"  #{n['id']}: {n['content'][:150]}{source_tag}\n"

    return [TextContent(type="text", text=text)]


register_tool(
    Tool(
        name="add_property_note",
        description="Add a freeform note to a property. Notes are included in property recaps and AI summaries. "
                    "Voice: 'Note that the owner mentioned a roof leak on property 5' or "
                    "'Add a note to property 3: seller is motivated, wants to close by March'",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer", "description": "Property ID to add note to"},
                "content": {"type": "string", "description": "The note content (freeform text)"},
                "source": {
                    "type": "string",
                    "enum": ["voice", "manual", "ai", "phone_call", "system"],
                    "default": "voice",
                    "description": "Where the note came from",
                },
                "created_by": {"type": "string", "description": "Who created the note", "default": "voice assistant"},
            },
            "required": ["property_id", "content"],
        },
    ),
    handle_add_property_note,
)

register_tool(
    Tool(
        name="list_property_notes",
        description="List all notes for a property. Shows freeform notes added via voice, AI, or manually. "
                    "Voice: 'What notes do we have on property 5?' or 'Read me the notes for 123 Main St'",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer", "description": "Property ID"},
                "limit": {"type": "integer", "default": 10, "description": "Max notes to return"},
            },
            "required": ["property_id"],
        },
    ),
    handle_list_property_notes,
)
