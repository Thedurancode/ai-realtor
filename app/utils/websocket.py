"""WebSocket utility functions for routers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.main import WebSocketManager


def get_ws_manager() -> "WebSocketManager":
    """
    Get the WebSocket manager instance from main app.

    This is a shared utility to avoid duplicating this import pattern
    across multiple router files.

    Returns:
        WebSocketManager: The global WebSocket manager instance
    """
    from app.main import ws_manager
    return ws_manager
