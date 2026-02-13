"""Context auto-injection for MCP tool responses.

Enriches tool outputs with relevant conversation context so the voice
assistant can reference prior interactions naturally:
- "This is the property at 123 Main St we were just discussing."
- "Recent activity: Contract signed 2 hours ago."
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from mcp.types import TextContent

from .http_client import api_get, api_post

# Tools that should receive property-level context hints
_PROPERTY_CONTEXT_TOOLS = {
    "enrich_property", "skip_trace_property", "get_property",
    "check_property_contract_readiness", "check_property_contract_readiness_voice",
    "attach_required_contracts", "ai_suggest_contracts",
    "apply_ai_contract_suggestions", "generate_property_recap",
    "get_property_recap", "make_property_phone_call",
}

# Tools that should skip context injection entirely
_SKIP_TOOLS = {
    "get_conversation_history", "what_did_we_discuss", "clear_conversation_history",
    "poll_for_updates", "get_notification_summary", "list_notifications",
    "list_voice_campaigns",
}


def _human_time_ago(timestamp_str: str) -> str:
    try:
        ts = timestamp_str.replace("Z", "+00:00")
        if "+" not in ts and ts.count("-") < 3:
            ts += "+00:00"
        timestamp = datetime.fromisoformat(ts)
        now = datetime.now(timezone.utc)
        diff = now - timestamp
        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"{minutes}m ago"
        return "just now"
    except Exception:
        return "recently"


def _extract_property_id(tool_name: str, arguments: dict[str, Any]) -> int | None:
    """Try to extract property_id from tool arguments."""
    for key in ("property_id", "property_ref"):
        val = arguments.get(key)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                pass
    return None


def _get_session_state(session_id: str) -> dict[str, Any]:
    """Fetch current session state from memory graph. Returns {} on failure."""
    try:
        resp = api_get("/context/history/", params={"session_id": session_id, "limit": 3})
        resp.raise_for_status()
        history = resp.json()
        return {"recent_history": history}
    except Exception:
        return {}


def _get_related_notifications(property_id: int, limit: int = 3) -> str:
    """Fetch recent notifications for a property. Returns formatted text or ''."""
    try:
        resp = api_get("/notifications/", params={"limit": 30})
        resp.raise_for_status()
        all_notifs = resp.json()
        if not isinstance(all_notifs, list):
            return ""

        related = [n for n in all_notifs if n.get("property_id") == property_id][:limit]
        if not related:
            return ""

        lines = []
        for n in related:
            time_ago = _human_time_ago(n.get("created_at", ""))
            lines.append(f"  {n.get('icon', '')} {n.get('title', 'Update')} ({time_ago})")
        return "\n".join(lines)
    except Exception:
        return ""


def enrich_response(
    tool_name: str,
    arguments: dict[str, Any],
    result: list[TextContent],
    session_id: str = "mcp_session",
) -> list[TextContent]:
    """Append context hints to MCP tool output.

    Designed to be lightweight and fail-safe — never blocks or slows down
    the primary tool response.
    """
    if tool_name in _SKIP_TOOLS:
        return result
    if not result:
        return result

    hints: list[str] = []

    # Property-level context
    if tool_name in _PROPERTY_CONTEXT_TOOLS:
        property_id = _extract_property_id(tool_name, arguments)
        if property_id:
            notif_text = _get_related_notifications(property_id, limit=2)
            if notif_text:
                hints.append(f"Recent activity for this property:\n{notif_text}")

    if not hints:
        return result

    # Append context as a separate section at the end of the first result
    original = result[0].text if result else ""
    context_block = "\n\n---\n" + "\n".join(hints)
    enriched = original + context_block
    return [TextContent(type="text", text=enriched)] + result[1:]
