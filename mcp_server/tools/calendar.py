"""Calendar Integration MCP tools — Google Calendar sync and event management."""
from mcp.types import Tool, TextContent
from datetime import datetime, timedelta

from ..server import register_tool
from ..utils.http_client import api_get, api_post
from ..utils.property_resolver import resolve_property_id


async def handle_connect_calendar(arguments: dict) -> list[TextContent]:
    """Initiate Google Calendar OAuth connection."""
    response = api_get("/calendar/auth/url")
    response.raise_for_status()
    data = response.json()

    auth_url = data.get("auth_url")
    state = data.get("state")

    text = (
        "To connect your Google Calendar:\n\n"
        f"1. Visit this URL: {auth_url}\n"
        "2. Sign in with your Google account and grant permissions\n"
        "3. After authorization, your calendar will be automatically connected\n\n"
        f"State token: {state}\n\n"
        "Your calendar will be synced with tasks, follow-ups, and appointments."
    )
    return [TextContent(type="text", text=text)]


async def handle_create_calendar_event(arguments: dict) -> list[TextContent]:
    """Create a manual calendar event."""
    # Check if "all_parties" flag is set - means fetch all contacts for property
    all_parties = arguments.get("all_parties", False)

    body = {
        "title": arguments.get("title"),
        "description": arguments.get("description", ""),
        "location": arguments.get("location"),
        "start_time": arguments.get("start_time"),
        "end_time": arguments.get("end_time"),
        "all_day": arguments.get("all_day", False),
        "event_type": arguments.get("event_type", "other"),
        "reminder_minutes": arguments.get("reminder_minutes"),
    }

    # Add property_id if provided
    property_id = None
    if arguments.get("property_id"):
        property_id = arguments["property_id"]
        body["property_id"] = property_id
    elif arguments.get("address"):
        # Resolve property from address
        property_id = resolve_property_id(arguments)
        body["property_id"] = property_id

    # Fetch all contacts for property if all_parties is True
    attendees = arguments.get("attendees", [])
    if all_parties and property_id:
        # Get all contacts for this property
        contacts_response = api_get(f"/contacts/property/{property_id}")
        contacts_response.raise_for_status()
        contacts_data = contacts_response.json()

        contacts = contacts_data.get("contacts", [])
        for contact in contacts:
            email = contact.get("email")
            if email:
                attendees.append({"email": email})

    # Add Google Meet option if creating meeting with multiple parties
    if arguments.get("create_meet") or (len(attendees) > 1 and arguments.get("add_meet_link", True)):
        body["create_meet"] = True

    # Add attendees if we have any
    if attendees:
        body["attendees"] = attendees

    response = api_post("/calendar/events", json=body)
    response.raise_for_status()
    data = response.json()

    if data.get("error"):
        return [TextContent(type="text", text=f"Error: {data['error']}")]

    title = data.get("title", "Event")
    start = data.get("start_time", "")
    meet_link = data.get("meet_link")

    text = f"Created calendar event: {title}"
    if start:
        text += f" at {start}"
    if attendees:
        text += f"\n👥 Invited {len(attendees)} attendee(s)"
    if meet_link:
        text += f"\n🎥 Google Meet: {meet_link}"
    text += "\n✓ Synced to your connected Google Calendar"

    return [TextContent(type="text", text=text)]


async def handle_list_calendar_events(arguments: dict) -> list[TextContent]:
    """List upcoming calendar events."""
    params = {}
    if arguments.get("days"):
        params["days"] = arguments["days"]
    if arguments.get("event_type"):
        params["event_type"] = arguments["event_type"]

    response = api_get("/calendar/events", params=params)
    response.raise_for_status()
    data = response.json()

    events = data.get("events", [])

    if not events:
        return [TextContent(type="text", text="No upcoming calendar events found.")]

    text = f"Upcoming events ({len(events)}):\n\n"
    for event in events:
        title = event.get("title", "Untitled")
        start = event.get("start_time", "")
        end = event.get("end_time", "")
        location = event.get("location", "")
        event_type = event.get("event_type", "")
        prop = event.get("property_address", "")

        text += f"• {title}"
        if start:
            text += f"\n  Time: {start}"
            if end and end != start:
                text += f" - {end}"
        if location:
            text += f"\n  Location: {location}"
        if event_type:
            text += f"\n  Type: {event_type}"
        if prop:
            text += f"\n  Property: {prop}"
        text += "\n"

    return [TextContent(type="text", text=text.strip())]


async def handle_sync_to_calendar(arguments: dict) -> list[TextContent]:
    """Manually trigger sync to Google Calendar."""
    response = api_get("/calendar/connections")
    response.raise_for_status()
    connections = response.json().get("connections", [])

    if not connections:
        return [TextContent(type="text", text="No calendar connections found. Connect your Google Calendar first.")]

    # Use first active connection
    connection = None
    for c in connections:
        if c.get("is_active") and c.get("sync_enabled"):
            connection = c
            break

    if not connection:
        return [TextContent(type="text", text="No active calendar connection with sync enabled.")]

    connection_id = connection["id"]
    response = api_post(f"/calendar/sync/{connection_id}")
    response.raise_for_status()
    data = response.json()

    synced = data.get("synced", 0)
    skipped = data.get("skipped", 0)
    errors = data.get("errors", [])

    text = f"Calendar sync complete: {synced} items synced"
    if skipped > 0:
        text += f", {skipped} skipped"
    if errors:
        text += f"\n\nErrors: {len(errors)}"
        for error in errors[:3]:
            text += f"\n- {error}"

    return [TextContent(type="text", text=text)]


async def handle_list_calendars(arguments: dict) -> list[TextContent]:
    """List connected calendar accounts."""
    response = api_get("/calendar/connections")
    response.raise_for_status()
    data = response.json()

    connections = data.get("connections", [])

    if not connections:
        return [TextContent(type="text", text="No calendar connections found. Use 'connect_calendar' to add one.")]

    text = f"Calendar connections ({len(connections)}):\n\n"
    for conn in connections:
        provider = conn.get("provider", "Unknown").capitalize()
        name = conn.get("calendar_name", "Primary")
        status = "Active" if conn.get("is_active") else "Inactive"
        sync_status = "On" if conn.get("sync_enabled") else "Off"
        last_sync = conn.get("last_sync_at", "Never")

        text += f"• {provider} Calendar ({name})\n"
        text += f"  Status: {status}\n"
        text += f"  Sync: {sync_status}\n"
        text += f"  Last sync: {last_sync}\n"

        # Show sync settings
        settings = []
        if conn.get("sync_tasks"):
            settings.append("tasks")
        if conn.get("sync_follow_ups"):
            settings.append("follow-ups")
        if conn.get("sync_appointments"):
            settings.append("appointments")
        if conn.get("sync_contracts"):
            settings.append("contracts")

        if settings:
            text += f"  Syncing: {', '.join(settings)}\n"
        text += "\n"

    return [TextContent(type="text", text=text.strip())]


async def handle_disconnect_calendar(arguments: dict) -> list[TextContent]:
    """Disconnect a calendar account."""
    connection_id = arguments.get("connection_id")

    if not connection_id:
        # List connections first
        response = api_get("/calendar/connections")
        response.raise_for_status()
        connections = response.json().get("connections", [])

        if not connections:
            return [TextContent(type="text", text="No calendar connections found.")]

        if len(connections) == 1:
            connection_id = connections[0]["id"]
        else:
            text = "Multiple calendars connected. Please specify connection_id:\n\n"
            for conn in connections:
                provider = conn.get("provider", "Unknown").capitalize()
                name = conn.get("calendar_name", "Primary")
                text += f"ID {conn['id']}: {provider} ({name})\n"
            return [TextContent(type="text", text=text)]

    response = api_post(f"/calendar/connections/{connection_id}/disconnect")
    response.raise_for_status()
    data = response.json()

    if data.get("error"):
        return [TextContent(type="text", text=f"Error: {data['error']}")]

    return [TextContent(type="text", text="Calendar disconnected successfully.")]


async def handle_update_calendar_event(arguments: dict) -> list[TextContent]:
    """Update an existing calendar event."""
    event_id = arguments.get("event_id")
    if not event_id:
        return [TextContent(type="text", text="Error: event_id is required")]

    body = {}
    if arguments.get("title"):
        body["title"] = arguments["title"]
    if arguments.get("description"):
        body["description"] = arguments["description"]
    if arguments.get("location"):
        body["location"] = arguments["location"]
    if arguments.get("start_time"):
        body["start_time"] = arguments["start_time"]
    if arguments.get("end_time"):
        body["end_time"] = arguments["end_time"]

    if not body:
        return [TextContent(type="text", text="Error: No fields to update")]

    response = api_post(f"/calendar/events/{event_id}", json=body)
    response.raise_for_status()
    data = response.json()

    if data.get("error"):
        return [TextContent(type="text", text=f"Error: {data['error']}")]

    event = data.get("event", {})
    title = event.get("title", "Event")

    return [TextContent(type="text", text=f"Updated calendar event: {title}")]


async def handle_delete_calendar_event(arguments: dict) -> list[TextContent]:
    """Delete a calendar event."""
    event_id = arguments.get("event_id")
    if not event_id:
        return [TextContent(type="text", text="Error: event_id is required")]

    response = api_post(f"/calendar/events/{event_id}/delete")
    response.raise_for_status()
    data = response.json()

    if data.get("error"):
        return [TextContent(type="text", text=f"Error: {data['error']}")]

    return [TextContent(type="text", text="Calendar event deleted successfully.")]


# ── Registration ──

register_tool(
    Tool(
        name="connect_calendar",
        description=(
            "Initiate Google Calendar OAuth connection. Returns an authorization URL "
            "to visit in your browser. After granting permission, your calendar will "
            "automatically sync tasks, follow-ups, and appointments. "
            "Voice: 'Connect my Google Calendar', 'Add calendar integration'"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_connect_calendar,
)

register_tool(
    Tool(
        name="create_calendar_event",
        description=(
            "Create a manual calendar event. Optionally link to a property. "
            "Automatically syncs to connected Google Calendar. "
            "Can create Google Meet links for virtual meetings. "
            "Use 'all_parties: true' to automatically invite all contacts associated with a property. "
            "Voice: 'Schedule a showing for 123 Main St tomorrow at 2pm', "
            "'Add closing appointment for property 5 on Friday at 10am', "
            "'Create meeting with seller next Tuesday at 3pm', "
            "'Add all parties for 142 Throop for meeting on Saturday', "
            "'Set up a Zoom call with buyer tomorrow' (creates Google Meet)"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Event title (e.g., 'Property Showing', 'Closing', 'Meeting')",
                },
                "description": {"type": "string", "description": "Event description"},
                "location": {"type": "string", "description": "Event location"},
                "start_time": {
                    "type": "string",
                    "description": "Start time (ISO format or natural language like 'tomorrow at 2pm')",
                },
                "end_time": {
                    "type": "string",
                    "description": "End time (ISO format or natural language)",
                },
                "all_day": {"type": "boolean", "description": "Is this an all-day event?", "default": False},
                "event_type": {
                    "type": "string",
                    "description": "Event type",
                    "enum": ["showing", "inspection", "closing", "meeting", "other"],
                    "default": "other",
                },
                "property_id": {"type": "number", "description": "Property ID to link event to"},
                "address": {
                    "type": "string",
                    "description": "Property address to resolve to property_id",
                },
                "reminder_minutes": {
                    "type": "number",
                    "description": "Reminder before event in minutes (default: 15)",
                    "default": 15,
                },
                "create_meet": {
                    "type": "boolean",
                    "description": "Create a Google Meet link for this event",
                    "default": False,
                },
                "all_parties": {
                    "type": "boolean",
                    "description": "Auto-invite all contacts associated with the property",
                    "default": False,
                },
                "attendees": {
                    "type": "array",
                    "description": "List of attendees (email addresses)",
                    "items": {"type": "object", "properties": {"email": {"type": "string"}}},
                },
            },
            "required": ["title", "start_time"],
        },
    ),
    handle_create_calendar_event,
)

register_tool(
    Tool(
        name="list_calendar_events",
        description=(
            "List upcoming calendar events. Filter by days ahead or event type. "
            "Voice: 'What's on my calendar today?', 'Show me this week's events', "
            "'Upcoming showings', 'Any appointments this week?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "days": {
                    "type": "number",
                    "description": "Number of days ahead to look (default: 7)",
                    "default": 7,
                },
                "event_type": {
                    "type": "string",
                    "description": "Filter by event type",
                    "enum": ["showing", "inspection", "closing", "meeting", "other"],
                },
            },
        },
    ),
    handle_list_calendar_events,
)

register_tool(
    Tool(
        name="sync_to_calendar",
        description=(
            "Manually trigger sync of pending tasks, follow-ups, and appointments "
            "to connected Google Calendar. "
            "Voice: 'Sync my calendar', 'Update Google Calendar', 'Sync tasks to calendar'"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_sync_to_calendar,
)

register_tool(
    Tool(
        name="list_calendars",
        description=(
            "List all connected calendar accounts and their sync settings. "
            "Voice: 'Show my calendars', 'What calendars are connected?', "
            "'Calendar connections'"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_list_calendars,
)

register_tool(
    Tool(
        name="disconnect_calendar",
        description=(
            "Disconnect a calendar account. Stops syncing but doesn't delete existing events. "
            "Voice: 'Disconnect my calendar', 'Remove calendar integration'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "connection_id": {
                    "type": "number",
                    "description": "Calendar connection ID (optional if only one calendar)",
                },
            },
        },
    ),
    handle_disconnect_calendar,
)

register_tool(
    Tool(
        name="update_calendar_event",
        description=(
            "Update an existing calendar event. Only include fields to change. "
            "Voice: 'Reschedule the showing to tomorrow', "
            "'Change meeting time to 3pm', 'Update event location'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "number",
                    "description": "Calendar event ID to update",
                },
                "title": {"type": "string", "description": "New event title"},
                "description": {"type": "string", "description": "New description"},
                "location": {"type": "string", "description": "New location"},
                "start_time": {"type": "string", "description": "New start time"},
                "end_time": {"type": "string", "description": "New end time"},
            },
            "required": ["event_id"],
        },
    ),
    handle_update_calendar_event,
)

register_tool(
    Tool(
        name="delete_calendar_event",
        description=(
            "Delete a calendar event. "
            "Voice: 'Cancel the showing', 'Delete calendar event', "
            "'Remove the appointment'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "number",
                    "description": "Calendar event ID to delete",
                },
            },
            "required": ["event_id"],
        },
    ),
    handle_delete_calendar_event,
)
