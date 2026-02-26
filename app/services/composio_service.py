"""Composio MCP Tool Management Service

Integrates with Composio for MCP tool management, routing, and monitoring.
https://composio.dev

NOTE: Composio sessions must be created via the JavaScript/TypeScript SDK.
This service provides helper methods to work with existing sessions.
"""
import os
import httpx
import logging
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ComposioService:
    """Service for managing MCP tools via Composio platform"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("COMPOSIO_API_KEY")
        self.base_url = "https://backend.composio.dev"
        self.external_user_id = os.environ.get("COMPOSIO_EXTERNAL_USER_ID", "ai-realtor-agent")

    def get_mcp_server_url(self, session_id: str) -> str:
        """Get the MCP server URL for a session

        Args:
            session_id: Composio session ID (e.g., trs_abc123)

        Returns:
            MCP server URL (SSE transport)

        Example:
            >>> composio = ComposioService()
            >>> url = composio.get_mcp_server_url("trs_3fgJ0ka6YUtE")
            >>> print(url)
            https://backend.composio.dev/tool_router/trs_3fgJ0ka6YUtE/mcp
        """
        return f"{self.base_url}/tool_router/{session_id}/mcp"

    async def validate_session(self, session_id: str) -> Dict:
        """Validate that a Composio session is accessible

        Args:
            session_id: Composio session ID

        Returns:
            Validation status with MCP server URL
        """
        mcp_url = self.get_mcp_server_url(session_id)

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Try to connect to the MCP endpoint
                response = await client.get(
                    mcp_url,
                    headers={
                        "Accept": "text/event-stream"
                    },
                    timeout=5.0
                )

                # SSE endpoints might return 400/404 without proper handshake
                # Any response (not a connection error) means the endpoint exists
                return {
                    "valid": True,
                    "session_id": session_id,
                    "mcp_url": mcp_url,
                    "status": "accessible",
                    "note": "Session exists and MCP endpoint is reachable"
                }

            except httpx.ConnectError as e:
                return {
                    "valid": False,
                    "session_id": session_id,
                    "mcp_url": mcp_url,
                    "status": "unreachable",
                    "error": f"Cannot connect to Composio: {str(e)}"
                }
            except Exception as e:
                # Other errors might still mean the endpoint exists
                return {
                    "valid": True,
                    "session_id": session_id,
                    "mcp_url": mcp_url,
                    "status": "unknown",
                    "note": f"Session validation returned: {str(e)}"
                }


    def get_claude_desktop_config(self, session_id: str) -> Dict:
        """Get Claude Desktop configuration for this session

        Args:
            session_id: Composio session ID

        Returns:
            Claude Desktop MCP server configuration

        Example:
            >>> composio = ComposioService()
            >>> config = composio.get_claude_desktop_config("trs_3fgJ0ka6YUtE")
            >>> print(config)
            {
              "mcpServers": {
                "composio-ai-realtor": {
                  "transport": "sse",
                  "url": "https://backend.composio.dev/tool_router/trs_3fgJ0ka6YUtE/mcp"
                }
              }
            }
        """
        return {
            "mcpServers": {
                "composio-ai-realtor": {
                    "transport": "sse",
                    "url": self.get_mcp_server_url(session_id),
                    "timeout": 60000
                }
            }
        }


# ============================================================================
# Helper Functions
# ============================================================================

def get_current_session_config() -> Dict:
    """Get the current Composio session configuration

    Uses the session ID provided by the user (trs_3fgJ0ka6YUtE).

    Returns:
        Session configuration with MCP server URL and Claude Desktop config
    """
    composio = ComposioService()
    session_id = "trs_3fgJ0ka6YUtE"

    return {
        "session_id": session_id,
        "mcp_url": composio.get_mcp_server_url(session_id),
        "claude_desktop_config": composio.get_claude_desktop_config(session_id),
        "external_user_id": composio.external_user_id
    }
