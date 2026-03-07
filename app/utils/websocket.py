"""WebSocket utility functions for routers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.websocket import ConnectionManager


def get_ws_manager() -> "ConnectionManager":
    """Get the WebSocket manager instance."""
    from app.websocket import manager
    return manager
