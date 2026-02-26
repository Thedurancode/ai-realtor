"""Telnyx Voice API - Direct telephony integration."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging

from app.database import get_db
from app.services.telnyx_service import get_telnyx_service
from app.models import Agent, ScheduledTask, PhoneCall, Property
from app.auth import get_current_agent

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/telnyx", tags=["Telnyx Voice"])


# ── Request Schemas ──


class TelnyxCallRequest(BaseModel):
    """Request to initiate a Telnyx call."""

    to: str = Field(..., description="Destination phone number (E.164 format)")
    script: str = Field(..., description="Text script for the call")
    from_number: Optional[str] = Field(None, description="Caller ID number (optional)")
    property_id: Optional[int] = Field(None, description="Property ID for context")
    questions: Optional[List[str]] = Field(default_factory=list, description="Questions to ask")
    detect_machine: bool = Field(True, description="Enable answering machine detection")
    record_call: bool = Field(True, description="Enable call recording")
    webhook_url: Optional[str] = Field(None, description="Custom webhook URL")


class TelnyxSpeakRequest(BaseModel):
    """Request to speak text to an active call."""

    text: str = Field(..., description="Text to speak")
    language: str = Field("en-US", description="Language code")
    voice: str = Field("female", description="Voice type (male/female)")


class TelnyxGatherRequest(BaseModel):
    """Request to gather audio input from a call."""

    prompt: str = Field(..., description="Prompt text to speak")
    max_digits: int = Field(10, description="Maximum DTMF digits")
    timeout_secs: int = Field(30, description="Timeout in seconds")


# ── Response Schemas ──


class TelnyxCallResponse(BaseModel):
    """Response from call initiation."""

    call_id: str
    call_session_id: str
    call_leg_id: str
    status: str
    provider: str
    to: str
    from_number: str


class TelnyxStatusResponse(BaseModel):
    """Response from call status check."""

    call_id: str
    status: str
    state: str
    is_alive: bool
    duration_seconds: int
    start_time: Optional[str]
    end_time: Optional[str]
    recording_id: Optional[str]
    recording_enabled: bool


# ── API Endpoints ──


@router.post("/calls", response_model=TelnyxCallResponse)
async def create_telnyx_call(
    request: TelnyxCallRequest,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    """
    Initiate an outbound call using Telnyx API.

    Features:
    - Answering machine detection
    - Call recording
    - Text-to-speech for scripts
    - Property context tracking
    - Question list for AI agent
    - Saves to PhoneCall table for history
    """
    service = get_telnyx_service()

    # Verify property ownership if property_id provided
    if request.property_id:
        property = db.query(Property).filter(Property.id == request.property_id).first()
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")
        if property.agent_id != current_agent.id:
            raise HTTPException(status_code=403, detail="Not authorized to call this property")

    try:
        result = await service.create_call(
            to=request.to,
            script=request.script,
            from_number=request.from_number,
            property_id=request.property_id,
            questions=request.questions,
            detect_machine=request.detect_machine,
            record_call=request.record_call,
            webhook_url=request.webhook_url,
        )

        # Save call to database with proper agent_id
        phone_call = PhoneCall(
            agent_id=current_agent.id,  # FIXED: Use authenticated agent's ID
            direction="outbound",
            phone_number=request.to,
            provider="telnyx",
            telnyx_call_id=result["call_id"],
            telnyx_call_session_id=result["call_session_id"],
            telnyx_call_leg_id=result["call_leg_id"],
            status="initiated",
            property_id=request.property_id,
            transcription=None,  # Will be updated by webhook
            recording_url=None,  # Will be updated by webhook
            created_at=datetime.utcnow(),
        )

        try:
            db.add(phone_call)
            db.commit()
            db.refresh(phone_call)
        except Exception as db_error:
            # Call was made but failed to save - log the error
            logger.error(f"Failed to save Telnyx call to database: {db_error}. Call ID: {result.get('call_id')}")
            raise HTTPException(
                status_code=500,
                detail=f"Call initiated but failed to save to database: {str(db_error)}"
            )

        return TelnyxCallResponse(
            call_id=result["call_id"],
            call_session_id=result["call_session_id"],
            call_leg_id=result["call_leg_id"],
            status=result["status"],
            provider=result["provider"],
            to=result["to"],
            from_number=result["from"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create call: {str(e)}")


@router.get("/calls/{call_control_id}", response_model=TelnyxStatusResponse)
async def get_telnyx_call_status(
    call_control_id: str,
    db: Session = Depends(get_db),
):
    """
    Get the status of a Telnyx call.

    Returns:
    - Current status (initiated, in_progress, completed, failed, no_answer)
    - Call duration
    - Recording information
    - Start and end times
    """
    service = get_telnyx_service()

    try:
        result = await service.get_call_status(call_control_id)

        return TelnyxStatusResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get call status: {str(e)}")


@router.post("/calls/{call_control_id}/hangup")
async def hangup_telnyx_call(
    call_control_id: str,
    db: Session = Depends(get_db),
):
    """
    Hang up an active Telnyx call.

    Use this to terminate a call that's in progress.
    """
    service = get_telnyx_service()

    try:
        result = await service.hangup_call(call_control_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to hangup call: {str(e)}")


@router.post("/calls/{call_control_id}/speak")
async def speak_to_telnyx_call(
    call_control_id: str,
    request: TelnyxSpeakRequest,
    db: Session = Depends(get_db),
):
    """
    Speak text to an active call using text-to-speech.

    Use this for dynamic prompts during a call.
    """
    service = get_telnyx_service()

    try:
        result = await service.speak_text(
            call_control_id=call_control_id,
            text=request.text,
            language=request.language,
            voice=request.voice,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to speak: {str(e)}")


@router.post("/calls/{call_control_id}/gather")
async def gather_from_telnyx_call(
    call_control_id: str,
    request: TelnyxGatherRequest,
    db: Session = Depends(get_db),
):
    """
    Gather audio input (DTMF or speech) from an active call.

    Use this to collect key presses or voice input.
    """
    service = get_telnyx_service()

    try:
        result = await service.gather_audio(
            call_control_id=call_control_id,
            prompt=request.prompt,
            max_digits=request.max_digits,
            timeout_secs=request.timeout_secs,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to gather: {str(e)}")


@router.get("/recordings/{recording_id}")
async def get_telnyx_recording(
    recording_id: str,
    db: Session = Depends(get_db),
):
    """
    Get a Telnyx call recording by ID.

    Returns the download URL and metadata.
    """
    service = get_telnyx_service()

    try:
        result = await service.get_recording(recording_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recording: {str(e)}")


@router.get("/phone-numbers")
async def list_telnyx_phone_numbers(
    limit: int = 20,
    status: str = "active",
    db: Session = Depends(get_db),
):
    """
    List available phone numbers in the Telnyx account.

    Useful for managing caller IDs and phone number inventory.
    """
    service = get_telnyx_service()

    try:
        numbers = await service.list_phone_numbers(limit=limit, status=status)
        return {"numbers": numbers, "count": len(numbers)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list numbers: {str(e)}")


# ── Webhook Handler ──


@router.post("/webhook")
async def telnyx_webhook(
    payload: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Handle webhooks from Telnyx for call events.

    Events handled:
    - call.initiated
    - call.answered
    - call.hangup
    - call.recording
    - call.machine.detected

    Automatically updates PhoneCall records and stores recordings.

    NOTE: This endpoint does not require authentication as it's called by Telnyx.
    Webhook signature verification should be implemented for production security.
    """
    event_type = payload.get("event_type", "unknown")
    call_data = payload.get("data", {})
    call_control_id = call_data.get("call_control_id")

    if not call_control_id:
        return {"status": "error", "message": "No call_control_id"}

    try:
        # Find the call in database
        phone_call = db.query(PhoneCall).filter(
            PhoneCall.telnyx_call_id == call_control_id
        ).first()

        if not phone_call:
            # Call might not be in our system yet
            logger.warning(f"Webhook received for unknown call_control_id: {call_control_id}")
            return {"status": "ignored", "message": "Call not found in database"}

        # Update based on event type
        if event_type == "call.initiated":
            phone_call.status = "in_progress"
            phone_call.started_at = datetime.utcnow()

        elif event_type == "call.answered":
            phone_call.status = "in_progress"
            phone_call.started_at = datetime.utcnow()

        elif event_type == "call.hangup":
            phone_call.status = "completed"
            phone_call.ended_at = datetime.utcnow()

            # Calculate duration
            if phone_call.started_at:
                duration = (datetime.utcnow() - phone_call.started_at).total_seconds()
                phone_call.duration_seconds = int(duration)

        elif event_type == "call.recording":
            # Store recording URL
            recording_url = call_data.get("recording_url")
            if recording_url:
                phone_call.recording_url = recording_url
                phone_call.recording_transcribed = False

        elif event_type == "call.machine.detected":
            # Answering machine detected
            phone_call.status = "no_answer"
            phone_call.ended_at = datetime.utcnow()

        # Commit with error handling
        try:
            db.commit()
        except Exception as commit_error:
            db.rollback()
            logger.error(f"Failed to commit webhook update: {commit_error}")
            return {"status": "error", "message": f"Database error: {str(commit_error)}"}

        return {
            "status": "received",
            "event_type": event_type,
            "call_control_id": call_control_id,
            "phone_call_id": phone_call.id,
        }

    except Exception as e:
        logger.error(f"Error processing Telnyx webhook: {e}")
        return {"status": "error", "message": f"Processing error: {str(e)}"}
