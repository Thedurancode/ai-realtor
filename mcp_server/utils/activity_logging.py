"""Activity event logging for MCP tool calls."""
from typing import Optional
from .http_client import api_post, api_patch


def log_activity_event(tool_name: str, metadata: dict = None) -> Optional[int]:
    """Log an activity event for MCP tool call."""
    try:
        response = api_post(
            "/activities/log",
            json={
                "tool_name": tool_name,
                "user_source": "Claude Desktop MCP",
                "event_type": "tool_call",
                "status": "pending",
                "metadata": metadata
            },
            timeout=1
        )
        if response.status_code == 200:
            return response.json().get("id")
    except Exception as e:
        print(f"Warning: Failed to log activity: {e}")
    return None


def update_activity_event(event_id: int, status: str, duration_ms: int, error_message: str = None):
    """Update activity event with result."""
    if not event_id:
        return
    try:
        api_patch(
            f"/activities/{event_id}",
            json={
                "status": status,
                "duration_ms": duration_ms,
                "error_message": error_message
            },
            timeout=1
        )
    except Exception as e:
        print(f"Warning: Failed to update activity: {e}")
