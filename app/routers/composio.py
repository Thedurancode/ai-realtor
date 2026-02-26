"""Composio MCP Integration Router

Provides endpoints for working with Composio MCP sessions.

IMPORTANT: Composio sessions must be created via the JavaScript/TypeScript SDK.
This router helps manage existing sessions and provides connection details.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.composio_service import (
    ComposioService,
    get_current_session_config
)

router = APIRouter(prefix="/composio", tags=["composio"])


# ============================================================================
# Request/Response Models
# ============================================================================

class SessionValidationRequest(BaseModel):
    session_id: str = Field(..., description="Composio session ID (e.g., trs_abc123)")


class ClaudeDesktopConfigRequest(BaseModel):
    session_id: str = Field(..., description="Composio session ID")


# ============================================================================
# Session Management Endpoints
# ============================================================================

@router.get("/session/current")
async def get_current_session():
    """Get current Composio session configuration

    Returns the session configuration for the pre-configured session ID.
    The session was created via the JavaScript SDK and is stored in the service.

    Returns:
        {
            "session_id": "trs_3fgJ0ka6YUtE",
            "mcp_url": "https://backend.composio.dev/tool_router/trs_3fgJ0ka6YUtE/mcp",
            "claude_desktop_config": {
                "mcpServers": {
                    "composio-ai-realtor": {
                        "transport": "sse",
                        "url": "https://backend.composio.dev/tool_router/trs_3fgJ0ka6YUtE/mcp",
                        "timeout": 60000
                    }
                }
            },
            "external_user_id": "ai-realtor-agent"
        }
    """
    try:
        config = get_current_session_config()
        return {
            "status": "success",
            "message": "Current Composio session configuration",
            **config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session config: {str(e)}")


@router.post("/session/validate")
async def validate_session(request: SessionValidationRequest):
    """Validate a Composio session

    Checks if the session is accessible and the MCP endpoint is reachable.

    Args:
        session_id: Composio session ID

    Returns:
        Validation status with MCP server URL
    """
    try:
        composio = ComposioService()
        validation = await composio.validate_session(request.session_id)

        return {
            "status": "validation_complete",
            **validation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/session/{session_id}/mcp-url")
async def get_mcp_url(session_id: str):
    """Get MCP server URL for a session

    Returns the SSE transport URL for connecting to the Composio MCP server.

    Args:
        session_id: Composio session ID

    Returns:
        {
            "session_id": "trs_3fgJ0ka6YUtE",
            "mcp_url": "https://backend.composio.dev/tool_router/trs_3fgJ0ka6YUtE/mcp",
            "transport": "sse",
            "description": "Use this URL in Claude Desktop configuration"
        }
    """
    try:
        composio = ComposioService()
        mcp_url = composio.get_mcp_server_url(session_id)

        return {
            "session_id": session_id,
            "mcp_url": mcp_url,
            "transport": "sse",
            "description": "Use this URL in Claude Desktop configuration",
            "usage": {
                "claude_desktop": {
                    "mcpServers": {
                        "composio-ai-realtor": {
                            "transport": "sse",
                            "url": mcp_url,
                            "timeout": 60000
                        }
                    }
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get MCP URL: {str(e)}")


@router.post("/session/{session_id}/claude-config")
async def get_claude_desktop_config(session_id: str):
    """Get Claude Desktop configuration for a session

    Returns the complete Claude Desktop configuration for connecting to this session.

    Args:
        session_id: Composio session ID

    Returns:
        Claude Desktop MCP server configuration ready to copy-paste
    """
    try:
        composio = ComposioService()
        config = composio.get_claude_desktop_config(session_id)

        return {
            "session_id": session_id,
            "claude_desktop_config": config,
            "instructions": {
                "step_1": "Open Claude Desktop Settings (Developer > Open Config Folder)",
                "step_2": "Edit claude_desktop_config.json",
                "step_3": "Add the config below to the 'mcpServers' object",
                "step_4": "Restart Claude Desktop",
                "step_5": "Your AI Realtor tools will be available!"
            },
            "config_json": config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@router.get("/health")
async def composio_health():
    """Check Composio service health

    Validates the current session and checks if Composio is accessible.
    """
    composio = ComposioService()
    try:
        config = get_current_session_config()
        validation = await composio.validate_session(config["session_id"])

        return {
            "status": "healthy" if validation["valid"] else "degraded",
            "composio_accessible": True,
            "session_id": config["session_id"],
            "mcp_url": config["mcp_url"],
            "validation": validation
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "composio_accessible": False,
            "error": str(e)
        }


@router.get("/")
async def composio_info():
    """Composio integration information

    Provides information about the Composio integration and how to use it.
    """
    return {
        "service": "Composio MCP Integration",
        "description": "Tool management and routing via Composio platform",
        "documentation": "https://docs.composio.dev",
        "important_notes": [
            "Composio sessions must be created via JavaScript/TypeScript SDK",
            "Use @composio/core npm package to create sessions",
            "This API helps manage existing sessions",
            "Direct MCP connection is also available (135+ tools)"
        ],
        "endpoints": {
            "GET /composio/session/current": "Get current session configuration",
            "POST /composio/session/validate": "Validate a session",
            "GET /composio/session/{id}/mcp-url": "Get MCP server URL",
            "POST /composio/session/{id}/claude-config": "Get Claude Desktop config",
            "GET /composio/health": "Health check"
        },
        "current_session": {
            "session_id": "trs_3fgJ0ka6YUtE",
            "created_via": "JavaScript SDK",
            "external_user_id": "ai-realtor-agent"
        },
        "alternative": {
            "direct_mcp": "Use direct MCP connection for 135+ AI Realtor tools",
            "config": "See CLAUDE.md for direct connection setup"
        }
    }
