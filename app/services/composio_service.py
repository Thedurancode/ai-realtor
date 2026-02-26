"""Composio MCP Tool Management Service

Integrates with Composio for MCP tool management, routing, and monitoring.
https://composio.dev
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

    async def create_session(self) -> Dict:
        """Create a Composio MCP session

        Returns:
            Session configuration with MCP server URL
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/tool_router/create",
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "externalUserId": self.external_user_id
                }
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"Created Composio session: {data.get('sessionId')}")

            return {
                "session_id": data.get("sessionId"),
                "mcp": data.get("mcp", {}),
                "external_user_id": self.external_user_id
            }

    async def get_session_status(self, session_id: str) -> Dict:
        """Get session status from Composio

        Args:
            session_id: Composio session ID

        Returns:
            Session status and configuration
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/tool_router/status/{session_id}",
                headers={
                    "X-API-Key": self.api_key
                }
            )
            response.raise_for_status()
            return response.json()

    async def list_available_tools(self, session_id: str) -> List[Dict]:
        """List available MCP tools in session

        Args:
            session_id: Composio session ID

        Returns:
            List of available tools
        """
        session_data = await self.get_session_status(session_id)

        # Extract MCP server configuration
        mcp_config = session_data.get("mcp", {})
        tools = mcp_config.get("tools", [])

        logger.info(f"Found {len(tools)} tools in session {session_id}")

        return tools

    async def execute_tool(
        self,
        session_id: str,
        tool_name: str,
        parameters: Dict
    ) -> Dict:
        """Execute an MCP tool through Composio

        Args:
            session_id: Composio session ID
            tool_name: Name of the tool to execute
            parameters: Tool parameters

        Returns:
            Tool execution result
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/tool_router/execute",
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "sessionId": session_id,
                    "tool": tool_name,
                    "parameters": parameters
                }
            )
            response.raise_for_status()
            return response.json()

    async def register_mcp_server(
        self,
        server_name: str,
        server_command: str,
        server_args: List[str]
    ) -> Dict:
        """Register a new MCP server with Composio

        Args:
            server_name: Name for the MCP server
            server_command: Command to start the server
            server_args: Arguments to pass to the command

        Returns:
            Registration confirmation
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/tool_router/register",
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "externalUserId": self.external_user_id,
                    "serverName": server_name,
                    "serverCommand": server_command,
                    "serverArgs": server_args
                }
            )
            response.raise_for_status()
            return response.json()

    def get_mcp_server_url(self, session_id: str) -> str:
        """Get the MCP server URL for a session

        Args:
            session_id: Composio session ID

        Returns:
            MCP server URL (SSE transport)
        """
        # Format: https://backend.composio.dev/tool_router/{session_id}/mcp
        return f"{self.base_url}/tool_router/{session_id}/mcp"


# ============================================================================
# Helper Functions
# ============================================================================

async def setup_composio_mcp_session() -> Dict:
    """Create and configure Composio MCP session

    Returns:
        Session configuration with MCP server URL
    """
    composio = ComposioService()
    session = await composio.create_session()

    logger.info(f"Composio MCP session created: {session['session_id']}")
    logger.info(f"MCP Server URL: {composio.get_mcp_server_url(session['session_id'])}")

    return session


async def register_ai_realtor_mcp_server() -> Dict:
    """Register the AI Realtor MCP server with Composio

    The AI Realtor MCP server provides tools for:
    - Property management
    - Contract handling
    - Skip trace
    - Voice calls
    - And 130+ more tools

    Returns:
        Registration confirmation
    """
    composio = ComposioService()

    result = await composio.register_mcp_server(
        server_name="ai-realtor-mcp",
        server_command="python3",
        server_args=[
            "/Users/edduran/Documents/GitHub/ai-realtor/mcp_server/property_mcp.py"
        ]
    )

    logger.info(f"AI Realtor MCP server registered with Composio")
    return result
