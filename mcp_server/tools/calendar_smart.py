"""Smart Calendar Analysis - conflict detection and scheduling suggestions."""
from mcp.types import Tool, TextContent
from datetime import datetime, timedelta

from ..server import register_tool
from ..utils.http_client import api_get


async def handle_check_conflicts(arguments: dict) -> list[TextContent]:
    """Check for calendar conflicts and scheduling issues."""
    start_time = arguments.get("start_time")
    end_time = arguments.get("end_time")
    property_id = arguments.get("property_id")

    # Get upcoming events
    response = api_get("/calendar/events", params={"days": arguments.get("days", 14)})
    response.raise_for_status()
    data = response.json()

    events = data.get("events", [])

    if not events:
        return [TextContent(type="text", text="No existing events to check for conflicts.")]

    # Parse the proposed meeting time
    proposed_start = None
    proposed_end = None
    if start_time:
        # Try to parse as ISO or natural language
        try:
            proposed_start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        except:
            # Natural language - approximate
            proposed_start = datetime.now() + timedelta(days=1)  # Default to tomorrow

        if end_time:
            try:
                proposed_end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            except:
                proposed_end = proposed_start + timedelta(hours=1)  # Default 1 hour

    conflicts = []
    warnings = []
    suggestions = []

    for event in events:
        event_start = datetime.fromisoformat(event.get("start_time").replace("Z", "+00:00")) if event.get("start_time") else None
        event_end = datetime.fromisoformat(event.get("end_time").replace("Z", "+00:00")) if event.get("end_time") else None
        event_title = event.get("title", "Unknown")
        event_type = event.get("event_type", "")

        if not event_start or not event_end:
            continue

        # Check for direct conflicts (overlapping times)
        if proposed_start and proposed_end:
            if (proposed_start < event_end and proposed_end > event_start):
                conflicts.append({
                    "event": event_title,
                    "time": f"{event_start.strftime('%a %I:%M %p')} - {event_end.strftime('%I:%M %p')}",
                    "type": event_type,
                })

            # Check for tight scheduling (less than 30 min between events)
            time_gap = (event_start - proposed_end).total_seconds() / 60
            if 0 <= time_gap < 30:
                warnings.append({
                    "event": event_title,
                    "issue": f"Only {int(time_gap)} minutes between meetings",
                    "suggestion": f"Add buffer time or reschedule to {event_start.strftime('%a %I:%M %p')}"
                })

            # Check for same-day property showing conflicts
            if property_id and event.get("property_id") == property_id:
                if event_start.date() == proposed_start.date():
                    warnings.append({
                        "event": event_title,
                        "issue": "Another event for this property on the same day",
                        "suggestion": f"Consider combining or spacing out property events"
                    })

        # Check for back-to-back showings (no travel time)
        if event_type == "showing":
            for other_event in events:
                if other_event.get("id") == event.get("id"):
                    continue
                if other_event.get("event_type") != "showing":
                    continue

                other_start = datetime.fromisoformat(other_event.get("start_time").replace("Z", "+00:00")) if other_event.get("start_time") else None
                if not other_start:
                    continue

                # If showings are less than 1 hour apart and different properties
                time_diff = abs((other_start - event_end).total_seconds() / 60) if event_end else 999
                if 0 < time_diff < 60 and other_event.get("property_id") != event.get("property_id"):
                    warnings.append({
                        "event": f"{event_title} and {other_event.get('title')}",
                        "issue": f"Only {int(time_diff)} min between showings at different properties",
                        "suggestion": "Allow at least 1 hour for travel between showings"
                    })

    # Find good time slots if there are conflicts
    if conflicts:
        suggestions = _find_available_slots(events, proposed_start or datetime.now(), duration_hours=1)

    # Build response
    text = ""
    if conflicts:
        text += f"⚠️ Found {len(conflicts)} conflict(s):\n\n"
        for c in conflicts:
            text += f"**{c['event']}** ({c['type']})\n"
            text += f"   Time: {c['time']}\n\n"
    else:
        text += "✅ No direct conflicts found!\n\n"

    if warnings:
        text += f"⚡ {len(warnings)} scheduling issue(s) to consider:\n\n"
        for w in warnings:
            text += f"**{w['event']}**\n"
            text += f"   Issue: {w['issue']}\n"
            if w.get("suggestion"):
                text += f"   💡 {w['suggestion']}\n"
            text += "\n"

    if suggestions:
        text += "📅 Suggested alternative times:\n\n"
        for slot in suggestions[:5]:
            text += f"• {slot}\n"

    if not conflicts and not warnings:
        text += "Your schedule looks clear! Ready to book."

    return [TextContent(type="text", text=text.strip())]


def _find_available_slots(events, reference_date, duration_hours=1):
    """Find available time slots that don't conflict."""
    from datetime import timedelta

    # Business hours: 9 AM - 6 PM
    business_start = 9
    business_end = 18

    # Check next 7 days
    slots = []
    for day_offset in range(7):
        check_date = reference_date + timedelta(days=day_offset)
        date_start = datetime(check_date.year, check_date.month, check_date.day, business_start)
        date_end = datetime(check_date.year, check_date.month, check_date.day, business_end)

        # Get events for this day
        day_events = []
        for event in events:
            event_start = datetime.fromisoformat(event.get("start_time").replace("Z", "+00:00")) if event.get("start_time") else None
            if event_start and event_start.date() == check_date.date():
                day_events.append(event_start)

        # Try hourly slots
        for hour in range(business_start, business_end - duration_hours + 1):
            slot_start = datetime(check_date.year, check_date.month, check_date.day, hour)
            slot_end = slot_start + timedelta(hours=duration_hours)

            # Check if this slot conflicts
            has_conflict = False
            for event_start in day_events:
                # Simplified - events assumed 1 hour
                if abs((event_start - slot_start).total_seconds()) < 3600:
                    has_conflict = True
                    break

            if not has_conflict:
                day_name = slot_start.strftime("%A")
                time_str = slot_start.strftime("%I:%M %p")
                slots.append(f"{day_name} at {time_str}")

                if len(slots) >= 10:  # Limit suggestions
                    break

        if len(slots) >= 10:
            break

    return slots


async def handle_suggest_meeting_time(arguments: dict) -> list[TextContent]:
    """Suggest optimal meeting times based on calendar and preferences."""
    duration = arguments.get("duration_minutes", 60)
    days_ahead = arguments.get("days_ahead", 7)
    preference = arguments.get("time_preference", "any")  # morning, afternoon, any

    # Get upcoming events
    response = api_get("/calendar/events", params={"days": days_ahead})
    response.raise_for_status()
    data = response.json()

    events = data.get("events", [])

    # Analyze and find best times
    business_hours = {
        "morning": (9, 12),
        "afternoon": (13, 17),
        "any": (9, 17)
    }

    start_hour, end_hour = business_hours.get(preference, business_hours["any"])

    slots = []
    now = datetime.now()

    for day_offset in range(days_ahead):
        check_date = now + timedelta(days=day_offset)

        # Skip weekends if preference is business hours
        if check_date.weekday() >= 5 and preference != "any":
            continue

        for hour in range(start_hour, end_hour):
            slot_start = datetime(check_date.year, check_date.month, check_date.day, hour)
            slot_end = slot_start + timedelta(minutes=duration)

            # Check for conflicts
            has_conflict = False
            for event in events:
                event_start = datetime.fromisoformat(event.get("start_time").replace("Z", "+00:00")) if event.get("start_time") else None
                event_end = datetime.fromisoformat(event.get("end_time").replace("Z", "+00:00")) if event.get("end_time") else None

                if event_start and event_end:
                    if slot_start < event_end and slot_end > event_start:
                        has_conflict = True
                        break

            if not has_conflict:
                day_name = slot_start.strftime("%A")
                date_str = slot_start.strftime("%b %d")
                time_str = slot_start.strftime("%I:%M %p")
                slots.append(f"{day_name}, {date_str} at {time_str}")

            if len(slots) >= 10:
                break

        if len(slots) >= 10:
            break

    if not slots:
        return [TextContent(type="text", text="No available time slots found in the next week. Try a different time range.")]

    text = f"📅 Best times for a {duration}-minute meeting ({preference} preference):\n\n"
    for i, slot in enumerate(slots[:10], 1):
        text += f"{i}. {slot}\n"

    return [TextContent(type="text", text=text)]


async def handle_analyze_schedule(arguments: dict) -> list[TextContent]:
    """Analyze calendar for patterns, workload, and suggestions."""
    days = arguments.get("days", 7)

    response = api_get("/calendar/events", params={"days": days})
    response.raise_for_status()
    data = response.json()

    events = data.get("events", [])

    if not events:
        return [TextContent(type="text", text="No events found to analyze.")]

    # Analyze patterns
    total_events = len(events)
    events_by_type = {}
    events_by_day = {}
    workload_by_day = {}

    for event in events:
        event_type = event.get("event_type", "other")
        events_by_type[event_type] = events_by_type.get(event_type, 0) + 1

        event_start = datetime.fromisoformat(event.get("start_time").replace("Z", "+00:00")) if event.get("start_time") else None
        if event_start:
            day_name = event_start.strftime("%A")
            events_by_day[day_name] = events_by_day.get(day_name, 0) + 1

            # Calculate workload (hours)
            event_end = datetime.fromisoformat(event.get("end_time").replace("Z", "+00:00")) if event.get("end_time") else None
            if event_end:
                duration_hours = (event_end - event_start).total_seconds() / 3600
                workload_by_day[day_name] = workload_by_day.get(day_name, 0) + duration_hours

    # Build insights
    text = f"📊 Schedule Analysis (Next {days} Days)\n\n"
    text += f"Total Events: {total_events}\n\n"

    if events_by_type:
        text += "**By Event Type:**\n"
        for event_type, count in sorted(events_by_type.items(), key=lambda x: x[1], reverse=True):
            text += f"• {event_type}: {count}\n"
        text += "\n"

    if events_by_day:
        text += "**Busiest Days:**\n"
        sorted_days = sorted(events_by_day.items(), key=lambda x: x[1], reverse=True)
        for day, count in sorted_days[:3]:
            hours = workload_by_day.get(day, 0)
            text += f"• {day}: {count} events ({hours:.1f} hours)\n"
        text += "\n"

    # Find least busy days
    if workload_by_day:
        text += "**Lightest Days (Good for scheduling):**\n"
        sorted_by_hours = sorted(workload_by_day.items(), key=lambda x: x[1])
        for day, hours in sorted_by_hours[:3]:
            text += f"• {day}: {hours:.1f} hours scheduled\n"
        text += "\n"

    # Recommendations
    text += "**💡 Recommendations:**\n"

    if workload_by_day:
        avg_hours = sum(workload_by_day.values()) / len(workload_by_day)
        max_hours = max(workload_by_day.values())

        if max_hours > avg_hours * 1.5:
            heavy_days = [day for day, hours in workload_by_day.items() if hours > avg_hours * 1.2]
            text += f"• Consider redistributing events from {', '.join(heavy_days)}\n"

    if events_by_type.get("showing", 0) > 5:
        text += "• High volume of showings - consider grouping by location\n"

    if total_events < 5:
        text += "• Light schedule - good time for prospecting or follow-ups\n"

    return [TextContent(type="text", text=text)]


# ── Registration ──

register_tool(
    Tool(
        name="check_calendar_conflicts",
        description=(
            "Check for calendar conflicts and scheduling issues before booking. "
            "Detects overlapping events, tight scheduling, back-to-back showings, "
            "and suggests alternative times. "
            "Voice: 'Check if Saturday at 2pm works', 'Any conflicts with tomorrow morning?', "
            "'Will Friday at 3pm conflict with anything?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "start_time": {
                    "type": "string",
                    "description": "Proposed start time (ISO format or natural language)",
                },
                "end_time": {
                    "type": "string",
                    "description": "Proposed end time",
                },
                "property_id": {
                    "type": "number",
                    "description": "Property ID (checks for same-day property events)",
                },
                "days": {
                    "type": "number",
                    "description": "Days ahead to check (default: 14)",
                    "default": 14,
                },
            },
        },
    ),
    handle_check_conflicts,
)

register_tool(
    Tool(
        name="suggest_meeting_time",
        description=(
            "Suggest optimal meeting times based on your calendar and preferences. "
            "Finds available slots that don't conflict with existing events. "
            "Voice: 'When's a good time for a 1-hour meeting?', 'Suggest a time this week', "
            "'Best time for a showing tomorrow?', 'When should I schedule a closing?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "duration_minutes": {
                    "type": "number",
                    "description": "Meeting duration in minutes (default: 60)",
                    "default": 60,
                },
                "days_ahead": {
                    "type": "number",
                    "description": "How many days ahead to look (default: 7)",
                    "default": 7,
                },
                "time_preference": {
                    "type": "string",
                    "description": "Time of day preference",
                    "enum": ["morning", "afternoon", "any"],
                    "default": "any",
                },
            },
        },
    ),
    handle_suggest_meeting_time,
)

register_tool(
    Tool(
        name="analyze_schedule",
        description=(
            "Analyze your calendar for patterns, workload distribution, and scheduling insights. "
            "Identifies busiest days, event type distribution, and provides recommendations. "
            "Voice: 'Analyze my schedule this week', 'How's my calendar looking?', "
            "'What's my workload like?', 'Review my schedule'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "days": {
                    "type": "number",
                    "description": "Number of days to analyze (default: 7)",
                    "default": 7,
                },
            },
        },
    ),
    handle_analyze_schedule,
)
