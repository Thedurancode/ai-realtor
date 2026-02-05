"""
Property Recap and Phone Call Endpoints

API endpoints for AI-generated property summaries and VAPI phone calls.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import requests

from app.database import get_db
from app.models.property import Property
from app.models.property_recap import PropertyRecap
from app.services.property_recap_service import property_recap_service
from app.services.vapi_service import vapi_service


router = APIRouter(prefix="/property-recap", tags=["property_recap"])


# Schemas
class RecapResponse(BaseModel):
    """Property recap response"""
    id: int
    property_id: int
    property_address: str
    recap_text: str
    voice_summary: str
    recap_context: dict
    version: int
    last_trigger: Optional[str]

    class Config:
        from_attributes = True


class PhoneCallRequest(BaseModel):
    """Phone call request"""
    phone_number: str  # E.164 format (e.g., +14155551234)
    call_purpose: Optional[str] = "property_update"  # property_update, contract_reminder, closing_ready, specific_contract_reminder, skip_trace_outreach
    custom_context: Optional[dict] = None  # Custom context for specific call types


class PhoneCallResponse(BaseModel):
    """Phone call response"""
    success: bool
    call_id: str
    status: str
    property_id: int
    property_address: str
    phone_number: str
    call_purpose: str
    message: str


# Endpoints

@router.post("/property/{property_id}/generate", response_model=RecapResponse)
async def generate_property_recap(
    property_id: int,
    trigger: str = "manual",
    db: Session = Depends(get_db)
):
    """
    Generate or update AI recap for a property.

    The recap includes:
    - Comprehensive property summary
    - Contract status and readiness
    - Voice-optimized summary for phone calls
    - Structured context for VAPI integration

    Trigger values: manual, property_created, property_updated, contract_signed, etc.
    """
    # Get property
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Generate recap
    recap = await property_recap_service.generate_recap(db, property, trigger)

    return RecapResponse(
        id=recap.id,
        property_id=recap.property_id,
        property_address=f"{property.address}, {property.city}, {property.state}",
        recap_text=recap.recap_text,
        voice_summary=recap.voice_summary,
        recap_context=recap.recap_context,
        version=recap.version,
        last_trigger=recap.last_trigger
    )


@router.get("/property/{property_id}", response_model=RecapResponse)
def get_property_recap(property_id: int, db: Session = Depends(get_db)):
    """
    Get existing recap for a property.

    Returns 404 if recap doesn't exist yet.
    Use POST /generate to create one.
    """
    # Get property
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Get recap
    recap = property_recap_service.get_recap(db, property_id)
    if not recap:
        raise HTTPException(
            status_code=404,
            detail="Recap not found. Use POST /generate to create one."
        )

    return RecapResponse(
        id=recap.id,
        property_id=recap.property_id,
        property_address=f"{property.address}, {property.city}, {property.state}",
        recap_text=recap.recap_text,
        voice_summary=recap.voice_summary,
        recap_context=recap.recap_context,
        version=recap.version,
        last_trigger=recap.last_trigger
    )


@router.post("/property/{property_id}/call", response_model=PhoneCallResponse)
async def make_property_call(
    property_id: int,
    call_request: PhoneCallRequest,
    db: Session = Depends(get_db)
):
    """
    Make a phone call about a property using VAPI.

    The call will include:
    - AI-generated property summary as context
    - Current contract status
    - Conversational AI that can answer questions

    Call purposes:
    - property_update: General property update call
    - contract_reminder: Remind about pending contracts
    - closing_ready: Celebrate that property is ready to close

    Phone number must be in E.164 format: +[country code][number]
    Example: +14155551234 for US number
    """
    # Get property
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Validate phone number format
    if not call_request.phone_number.startswith("+"):
        raise HTTPException(
            status_code=400,
            detail="Phone number must be in E.164 format (e.g., +14155551234)"
        )

    try:
        # Make call via VAPI
        result = await vapi_service.make_property_call(
            db=db,
            property=property,
            phone_number=call_request.phone_number,
            call_purpose=call_request.call_purpose,
            custom_context=call_request.custom_context
        )

        return PhoneCallResponse(
            success=result["success"],
            call_id=result["call_id"],
            status=result["status"],
            property_id=result["property_id"],
            property_address=result["property_address"],
            phone_number=result["phone_number"],
            call_purpose=result["call_purpose"],
            message=f"Call initiated successfully to {call_request.phone_number}"
        )

    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"VAPI API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error making call: {str(e)}"
        )


@router.get("/call/{call_id}/status")
async def get_call_status(call_id: str):
    """
    Get status of a VAPI call.

    Returns call details including:
    - Call status (queued, ringing, in-progress, ended)
    - Duration
    - Recording URL (if available)
    """
    try:
        status = await vapi_service.get_call_status(call_id)
        return status
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Call not found or VAPI error: {str(e)}"
        )


@router.post("/call/{call_id}/end")
async def end_call(call_id: str):
    """End an ongoing VAPI call"""
    try:
        result = await vapi_service.end_call(call_id)
        return {"success": True, "message": "Call ended", "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ending call: {str(e)}"
        )


@router.get("/call/{call_id}/recording")
async def get_call_recording(call_id: str):
    """Get recording URL for a completed call"""
    try:
        recording_url = await vapi_service.get_call_recording(call_id)

        if not recording_url:
            raise HTTPException(
                status_code=404,
                detail="Recording not available yet or call not recorded"
            )

        return {
            "call_id": call_id,
            "recording_url": recording_url
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting recording: {str(e)}"
        )
