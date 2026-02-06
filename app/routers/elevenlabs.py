"""
ElevenLabs Conversational AI Router

Endpoints for setting up and managing the ElevenLabs voice agent
that connects to the MCP SSE server for property management tools.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from app.rate_limit import limiter
from app.services.elevenlabs_service import elevenlabs_service


router = APIRouter(prefix="/elevenlabs", tags=["elevenlabs"])


class SetupRequest(BaseModel):
    system_prompt: Optional[str] = None
    first_message: Optional[str] = None


class ImportTwilioRequest(BaseModel):
    phone_number: str
    label: str = "Twilio"
    twilio_sid: str
    twilio_token: str


class CallRequest(BaseModel):
    phone_number: str
    custom_first_message: Optional[str] = None


class PromptUpdateRequest(BaseModel):
    prompt: str


@router.post("/setup", response_model=dict)
def setup_elevenlabs_agent(setup_data: Optional[SetupRequest] = None):
    """
    One-time setup: Register the MCP SSE server and create the voice agent.

    This connects ElevenLabs to the MCP server at ai-realtor.fly.dev:8001/sse,
    giving the agent access to all 36+ property management tools.

    Optionally pass system_prompt and/or first_message to customize the agent.

    Returns agent_id and widget embed HTML.
    """
    try:
        kwargs = {}
        if setup_data:
            if setup_data.system_prompt:
                kwargs["system_prompt"] = setup_data.system_prompt
            if setup_data.first_message:
                kwargs["first_message"] = setup_data.first_message
        result = elevenlabs_service.setup_agent(**kwargs)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")


@router.post("/import-twilio-number", response_model=dict)
def import_twilio_number(data: ImportTwilioRequest):
    """
    Import a Twilio phone number into ElevenLabs and assign it to the agent.

    After importing, the number can be used for outbound calls.
    """
    try:
        result = elevenlabs_service.import_twilio_number(
            phone_number=data.phone_number,
            label=data.label,
            twilio_sid=data.twilio_sid,
            twilio_token=data.twilio_token,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/assign-phone/{phone_number_id}", response_model=dict)
def assign_phone_to_agent(phone_number_id: str):
    """Assign an existing ElevenLabs phone number to the agent."""
    try:
        result = elevenlabs_service.assign_phone_number(phone_number_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assignment failed: {str(e)}")


@router.post("/call", response_model=dict)
@limiter.limit("3/minute")
def make_elevenlabs_call(request: Request, call_data: CallRequest):
    """
    Make an outbound call using the ElevenLabs voice agent.

    The agent will connect to the MCP SSE server and can use all tools
    during the conversation (look up properties, check contracts, etc.)

    Phone number must be in E.164 format: +14155551234
    """
    try:
        result = elevenlabs_service.make_call(
            phone_number=call_data.phone_number,
            custom_first_message=call_data.custom_first_message,
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
