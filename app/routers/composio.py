"""Composio MCP Integration Router

Manages MCP tool sessions and Composio platform integration.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.composio_service import (
    ComposioService,
    setup_composio_mcp_session,
    register_ai_realtor_mcp_server
)

router = APIRouter(prefix="/composio", tags=["composio"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateSessionRequest(BaseModel):
    external_user_id: str = Field(
        default="ai-realtor-agent",
        description="External user ID for Composio session"
    )


class ExecuteToolRequest(BaseModel):
    session_id: str = Field(..., description="Composio session ID")
    tool_name: str = Field(..., description="Name of tool to execute")
    parameters: dict = Field(default_factory=dict, description="Tool parameters")


class RegisterServerRequest(BaseModel):
    server_name: str = Field(..., description="MCP server name")
    server_command: str = Field(..., description="Command to start server")
    server_args: list[str] = Field(default_factory=list, description="Server arguments")


# ============================================================================
# Session Endpoints
# ============================================================================

@router.post("/session/create")
async def create_composio_session(request: CreateSessionRequest = None):
    """Create a Composio MCP session

    Creates a new session and returns the MCP server URL.
    The session connects to Composio's tool routing platform.

    Returns:
        Session configuration with MCP server URL for SSE transport

    Example response:
    {
        "session_id": "trs_3fgJ0ka6YUtE",
        "mcp": {...},
        "mcp_url": "https://backend.composio.dev/tool_router/trs_3fgJ0ka6YUtE/mcp"
    }
    """
    try:
        composio = ComposioService()

        # Use provided external_user_id or default
        external_id = request.external_user_id if request else "ai-realtor-agent"

        session = await composio.create_session()

        return {
            "session_id": session["session_id"],
            "mcp": session["mcp"],
            "mcp_url": f"https://backend.composio.dev/tool_router/{session['session_id']}/mcp",
            "external_user_id": session["external_user_id"],
            "message": "Session created successfully. Use mcp_url to connect via SSE transport."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get Composio session status

    Returns current status and configuration of the session.
    """
    try:
        composio = ComposioService()
        status = await composio.get_session_status(session_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/tools")
async def list_session_tools(session_id: str):
    """List available MCP tools in session

    Returns all tools available through this Composio session.
    """
    try:
        composio = ComposioService()
        tools = await composio.list_available_tools(session_id)
        return {
            "session_id": session_id,
            "total_tools": len(tools),
            "tools": tools
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/execute")
async def execute_composio_tool(request: ExecuteToolRequest):
    """Execute an MCP tool through Composio

    Routes the tool execution through Composio's platform.
    """
    try:
        composio = ComposioService()
        result = await composio.execute_tool(
            session_id=request.session_id,
            tool_name=request.tool_name,
            parameters=request.parameters
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/server/register")
async def register_mcp_server(request: RegisterServerRequest):
    """Register a new MCP server with Composio

    Registers an MCP server that can be managed through Composio.
    """
    try:
        composio = ComposioService()
        result = await composio.register_mcp_server(
            server_name=request.server_name,
            server_command=request.server_command,
            server_args=request.server_args
        )
        return {
            "message": "MCP server registered successfully",
            "server": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def composio_health():
    """Check if Composio API is accessible"""
    composio = ComposioService()
    try:
        # Try to create a test session
        session = await composio.create_session()
        return {
            "status": "healthy",
            "composio_accessible": True,
            "test_session_id": session.get("session_id"),
            "mcp_url": composio.get_mcp_server_url(session["session_id"])
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "composio_accessible": False,
            "error": str(e)
        }


# ============================================================================
# Quick Setup Endpoints
# ============================================================================

@router.post("/setup/ai-realtor")
async def setup_ai_realtor_composio():
    """Quick setup for AI Realtor with Composio

    One-time setup that:
    1. Creates a Composio session
    2. Returns MCP server URL
    3. Provides connection instructions

    Returns:
        Setup configuration and instructions
    """
    try:
        # Create session
        composio = ComposioService()
        session = await composio.create_session()

        # Get MCP URL
        mcp_url = composio.get_mcp_server_url(session["session_id"])

        return {
            "status": "success",
            "session": session,
            "mcp_url": mcp_url,
            "instructions": {
                "step_1": "Copy the MCP server URL below",
                "step_2": "Open Claude Desktop Settings",
                "step_3": "Add new MCP server with the URL",
                "step_4": "Name it 'AI Realtor - Composio'",
                "step_5": "Connect and enjoy 135+ AI Realtor tools!"
            },
            "claude_desktop_config": {
                "mcpServers": {
                    "ai-realtor-composio": {
                        "transport": "sse",
                        "url": mcp_url,
                        "timeout": 60000
                    }
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")
