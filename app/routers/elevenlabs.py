"""
ElevenLabs Conversational AI Router

Endpoints for setting up and managing the ElevenLabs voice agent
that connects to the MCP SSE server for property management tools.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.elevenlabs_service import elevenlabs_service


router = APIRouter(prefix="/elevenlabs", tags=["elevenlabs"])


class SetupResponse(BaseModel):
    mcp_server: dict
    agent: dict
    widget_html: str


class CallRequest(BaseModel):
    phone_number: str
    custom_first_message: Optional[str] = None


class PromptUpdateRequest(BaseModel):
    prompt: str


@router.post("/setup", response_model=dict)
def setup_elevenlabs_agent():
    """
    One-time setup: Register the MCP SSE server and create the voice agent.

    This connects ElevenLabs to the MCP server at ai-realtor.fly.dev:8001/sse,
    giving the agent access to all 36+ property management tools.

    Returns agent_id and widget embed HTML.
    """
    try:
        result = elevenlabs_service.setup_agent()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")


@router.post("/call", response_model=dict)
def make_elevenlabs_call(request: CallRequest):
    """
    Make an outbound call using the ElevenLabs voice agent.

    The agent will connect to the MCP SSE server and can use all tools
    during the conversation (look up properties, check contracts, etc.)

    Phone number must be in E.164 format: +14155551234
    """
    try:
        result = elevenlabs_service.make_call(
            phone_number=request.phone_number,
            custom_first_message=request.custom_first_message,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Call failed: {str(e)}")


@router.get("/agent", response_model=dict)
def get_elevenlabs_agent():
    """Get current ElevenLabs agent configuration and status."""
    try:
        return elevenlabs_service.get_agent_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/phone-numbers", response_model=list)
def list_elevenlabs_phone_numbers():
    """List available phone numbers for outbound calls."""
    try:
        return elevenlabs_service.list_phone_numbers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/agent/prompt", response_model=dict)
def update_elevenlabs_prompt(request: PromptUpdateRequest):
    """Update the voice agent's system prompt."""
    try:
        return elevenlabs_service.update_agent_prompt(request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/widget", response_model=dict)
def get_elevenlabs_widget():
    """
    Get the web widget embed configuration.

    Embed this HTML on any webpage to let users talk to the agent
    directly from their browser.
    """
    return elevenlabs_service.get_widget_config()
