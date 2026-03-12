"""
Property Recap and Phone Call Endpoints

API endpoints for AI-generated property summaries and VAPI phone calls.
"""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
import requests

from app.database import get_db
from app.rate_limit import limiter
from app.models.property import Property
from app.models.property_note import PropertyNote, NoteSource
from app.models.property_recap import PropertyRecap
from app.schemas.property_note import NoteCreate, NoteResponse, NoteListResponse
from app.services.property_recap_service import property_recap_service, regenerate_recap_background
from app.services.property_scoring_service import property_scoring_service
from app.services.vapi_service import vapi_service
from app.schemas.property_recap import RecapResponse, PhoneCallRequest, PhoneCallResponse


router = APIRouter(prefix="/property-recap", tags=["property-recap"])

@router.post("/property/{property_id}/generate", response_model=RecapResponse)
@limiter.limit("20/minute")
async def generate_property_recap(
    request: Request,
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


@router.post("/property/{property_id}/send-report")
@limiter.limit("10/minute")
def send_property_report(
    request: Request,
    property_id: int,
    report_type: str = "property_overview",
    db: Session = Depends(get_db),
):
    """
    Generate a PDF report and email it to the authenticated agent.

    report_type: property_overview (default). More types coming soon.
    """
    from app.services.pdf_report_service import generate_and_send
    from app.services.reports import list_report_types

    agent_id = getattr(request.state, "agent_id", None)
    if not agent_id:
        raise HTTPException(status_code=401, detail="Agent authentication required")

    try:
        result = generate_and_send(
            db=db,
            property_id=property_id,
            report_type=report_type,
            agent_id=agent_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send report: {result.get('email', {}).get('error', 'unknown error')}",
        )

    return {
        "success": True,
        "message": f"{report_type.replace('_', ' ').title()} sent to {result['agent_email']}",
        "filename": result["filename"],
        "report_type": result["report_type"],
        "property_id": result["property_id"],
        "property_address": result["property_address"],
        "available_report_types": list_report_types(),
    }


@router.post("/property/{property_id}/call", response_model=PhoneCallResponse)
@limiter.limit("5/minute")
async def make_property_call(
    request: Request,
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


# ── Property Notes (merged from property_notes.py) ──────────────

_notes_router = APIRouter(prefix="/property-notes", tags=["property-notes"])


@_notes_router.post("/", response_model=NoteResponse, status_code=201)
async def create_note(note: NoteCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Add a note to a property."""
    prop = db.query(Property).filter(Property.id == note.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    new_note = PropertyNote(
        property_id=note.property_id, content=note.content, source=note.source, created_by=note.created_by,
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    background_tasks.add_task(regenerate_recap_background, note.property_id, "note_added")
    return new_note


@_notes_router.get("/property/{property_id}", response_model=NoteListResponse)
def list_notes(property_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """List notes for a property, most recent first."""
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    notes = (
        db.query(PropertyNote).filter(PropertyNote.property_id == property_id)
        .order_by(PropertyNote.created_at.desc()).limit(limit).all()
    )
    if not notes:
        voice_summary = f"No notes for {prop.address}."
    elif len(notes) == 1:
        voice_summary = f"1 note for {prop.address}: {notes[0].content[:100]}"
    else:
        voice_summary = f"{len(notes)} notes for {prop.address}. Most recent: {notes[0].content[:100]}"
    return NoteListResponse(notes=notes, voice_summary=voice_summary)


@_notes_router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note."""
    note = db.query(PropertyNote).filter(PropertyNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return None


# ── Property Scoring (merged from property_scoring.py) ───────────

class BulkScoreRequest(BaseModel):
    property_ids: list[int] | None = None
    filters: dict | None = None


_scoring_router = APIRouter(prefix="/scoring", tags=["scoring"])


@_scoring_router.post("/property/{property_id}")
def score_property(property_id: int, db: Session = Depends(get_db)):
    """Score a single property (recalculates and saves)."""
    return property_scoring_service.score_property(db, property_id)


@_scoring_router.get("/property/{property_id}")
def get_score_breakdown(property_id: int, db: Session = Depends(get_db)):
    """Get stored score breakdown for a property (no recalculation)."""
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        return {"error": f"Property {property_id} not found"}
    if prop.deal_score is None:
        return {"error": "Property has not been scored yet. Use POST to score."}
    return {"property_id": prop.id, "address": prop.address, "score": prop.deal_score, "grade": prop.score_grade, "breakdown": prop.score_breakdown}


@_scoring_router.post("/bulk")
def bulk_score(request: BulkScoreRequest, db: Session = Depends(get_db)):
    """Score multiple properties."""
    return property_scoring_service.bulk_score(db, property_ids=request.property_ids, filters=request.filters)


@_scoring_router.get("/top")
def get_top_properties_scored(limit: int = Query(10, ge=1, le=100), min_score: float = Query(0, ge=0, le=100), db: Session = Depends(get_db)):
    """Get top-scored properties."""
    return property_scoring_service.get_top_properties(db, limit=limit, min_score=min_score)
