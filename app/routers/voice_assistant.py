"""Voice Assistant API - manage phone numbers and handle inbound calls."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agent import Agent
from app.models.phone_call import PhoneCall
from app.models.phone_number import PhoneNumber
from app.models.property import Property
from app.schemas.phone_number import PhoneNumberCreate, PhoneNumberResponse, PhoneNumberUpdate
from app.schemas.phone_call import PhoneCallResponse, PhoneCallListResponse
from app.services.voice_assistant_service import voice_assistant_service
from app.auth import get_current_agent

router = APIRouter()


# ── Phone Number Management ──

@router.post("/phone-numbers", response_model=PhoneNumberResponse)
def create_phone_number(
    data: PhoneNumberCreate,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Create a new phone number for inbound calling."""
    # Check if number already exists
    existing = db.query(PhoneNumber).filter(
        PhoneNumber.phone_number == data.phone_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already exists")

    # If setting as primary, uncheck other primary numbers
    if data.is_primary:
        db.query(PhoneNumber).filter(
            PhoneNumber.agent_id == current_agent.id,
            PhoneNumber.is_primary == True
        ).update({"is_primary": False})

    phone = PhoneNumber(
        agent_id=current_agent.id,
        **data.dict()
    )
    db.add(phone)
    db.commit()
    db.refresh(phone)

    return phone


@router.get("/phone-numbers", response_model=List[PhoneNumberResponse])
def list_phone_numbers(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """List all phone numbers for the current agent."""
    query = db.query(PhoneNumber).filter(
        PhoneNumber.agent_id == current_agent.id
    )

    if is_active is not None:
        query = query.filter(PhoneNumber.is_active == is_active)

    return query.all()


@router.get("/phone-numbers/{phone_id}", response_model=PhoneNumberResponse)
def get_phone_number(
    phone_id: int,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Get details of a specific phone number."""
    phone = db.query(PhoneNumber).filter(
        PhoneNumber.id == phone_id,
        PhoneNumber.agent_id == current_agent.id
    ).first()

    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found")

    return phone


@router.put("/phone-numbers/{phone_id}", response_model=PhoneNumberResponse)
def update_phone_number(
    phone_id: int,
    data: PhoneNumberUpdate,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Update phone number configuration."""
    phone = db.query(PhoneNumber).filter(
        PhoneNumber.id == phone_id,
        PhoneNumber.agent_id == current_agent.id
    ).first()

    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found")

    # If setting as primary, uncheck others
    if data.is_primary and not phone.is_primary:
        db.query(PhoneNumber).filter(
            PhoneNumber.agent_id == current_agent.id,
            PhoneNumber.is_primary == True
        ).update({"is_primary": False})

    for field, value in data.dict(exclude_unset=True).items():
        setattr(phone, field, value)

    db.commit()
    db.refresh(phone)

    return phone


@router.delete("/phone-numbers/{phone_id}")
def delete_phone_number(
    phone_id: int,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Delete a phone number."""
    phone = db.query(PhoneNumber).filter(
        PhoneNumber.id == phone_id,
        PhoneNumber.agent_id == current_agent.id
    ).first()

    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found")

    db.delete(phone)
    db.commit()

    return {"message": "Phone number deleted"}


@router.post("/phone-numbers/{phone_id}/set-primary")
def set_primary_number(
    phone_id: int,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Set a phone number as the primary number."""
    phone = db.query(PhoneNumber).filter(
        PhoneNumber.id == phone_id,
        PhoneNumber.agent_id == current_agent.id
    ).first()

    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found")

    # Uncheck all others
    db.query(PhoneNumber).filter(
        PhoneNumber.agent_id == current_agent.id,
        PhoneNumber.is_primary == True
    ).update({"is_primary": False})

    # Set this one as primary
    phone.is_primary = True
    db.commit()

    return {"message": f"{phone.phone_number} set as primary"}


# ── Inbound Call Handling ──

@router.post("/voice-assistant/incoming")
def handle_incoming_call(
    phone_number: str = Query(..., description="Caller's phone number"),
    vapi_call_id: str = Query(..., description="VAPI call UUID"),
    vapi_phone_id: str = Query(..., description="VAPI phone number ID"),
    db: Session = Depends(get_db)
):
    """Handle incoming call from VAPI webhook.

    This endpoint is called by VAPI when a call comes in.
    Returns AI configuration for the call.
    """
    try:
        response = voice_assistant_service.handle_incoming_call(
            db=db,
            phone_number=phone_number,
            vapi_call_id=vapi_call_id,
            vapi_phone_id=vapi_phone_id
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice-assistant/callback/{call_id}")
def handle_call_callback(
    call_id: int,
    event: str = Query(..., description="Event type: transcript, function_call, ended"),
    data: dict = None,
    db: Session = Depends(get_db)
):
    """Handle call progress events from VAPI.

    VAPI sends callbacks here as the call progresses:
    - transcript: Real-time transcription
    - function_call: AI wants to call a function
    - ended: Call completed
    """
    try:
        response = voice_assistant_service.handle_call_update(
            db=db,
            call_id=call_id,
            event=event,
            data=data or {}
        )
        return response or {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Call History & Analytics ──

@router.get("/phone-calls", response_model=PhoneCallListResponse)
def list_phone_calls(
    direction: Optional[str] = None,
    status: Optional[str] = None,
    intent: Optional[str] = None,
    property_id: Optional[int] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """List all phone calls for the current agent."""
    query = db.query(PhoneCall).filter(
        PhoneCall.agent_id == current_agent.id
    )

    if direction:
        query = query.filter(PhoneCall.direction == direction)
    if status:
        query = query.filter(PhoneCall.status == status)
    if intent:
        query = query.filter(PhoneCall.intent == intent)
    if property_id:
        query = query.filter(PhoneCall.property_id == property_id)

    total = query.count()
    calls = query.order_by(PhoneCall.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "calls": calls,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/phone-calls/{call_id}", response_model=PhoneCallResponse)
def get_phone_call(
    call_id: int,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Get details of a specific phone call."""
    call = db.query(PhoneCall).filter(
        PhoneCall.id == call_id,
        PhoneCall.agent_id == current_agent.id
    ).first()

    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    return call


@router.get("/phone-calls/recording/{call_id}")
def get_call_recording(
    call_id: int,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Get call recording URL."""
    call = db.query(PhoneCall).filter(
        PhoneCall.id == call_id,
        PhoneCall.agent_id == current_agent.id
    ).first()

    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    if not call.recording_url:
        raise HTTPException(status_code=404, detail="Recording not available")

    return {"recording_url": call.recording_url}


@router.get("/phone-calls/transcription/{call_id}")
def get_call_transcription(
    call_id: int,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Get call transcription."""
    call = db.query(PhoneCall).filter(
        PhoneCall.id == call_id,
        PhoneCall.agent_id == current_agent.id
    ).first()

    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    if not call.transcription:
        raise HTTPException(status_code=404, detail="Transcription not available")

    return {
        "transcription": call.transcription,
        "summary": call.summary
    }


# ── Call Analytics ──

@router.get("/phone-calls/analytics/overview")
def get_call_analytics(
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Get call analytics overview."""
    calls = db.query(PhoneCall).filter(
        PhoneCall.agent_id == current_agent.id
    ).all()

    # Calculate metrics
    total_calls = len(calls)
    inbound_calls = len([c for c in calls if c.direction == "inbound"])
    outbound_calls = len([c for c in calls if c.direction == "outbound"])

    completed_calls = len([c for c in calls if c.status == "completed"])
    missed_calls = len([c for c in calls if c.status in ["no_answer", "busy", "failed"]])

    total_duration = sum([c.duration_seconds or 0 for c in calls])
    total_cost = sum([c.cost or 0 for c in calls])

    # Intent breakdown
    intents = {}
    for call in calls:
        if call.intent:
            intents[call.intent] = intents.get(call.intent, 0) + 1

    # Outcome breakdown
    outcomes = {}
    for call in calls:
        if call.outcome:
            outcomes[call.outcome] = outcomes.get(call.outcome, 0) + 1

    return {
        "total_calls": total_calls,
        "inbound_calls": inbound_calls,
        "outbound_calls": outbound_calls,
        "completed_calls": completed_calls,
        "missed_calls": missed_calls,
        "completion_rate": round(completed_calls / total_calls * 100, 1) if total_calls > 0 else 0,
        "total_duration_minutes": round(total_duration / 60, 1),
        "total_cost": round(total_cost, 2),
        "intents": intents,
        "outcomes": outcomes
    }


@router.get("/phone-calls/analytics/by-property")
def get_property_call_analytics(
    property_id: Optional[int] = None,
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Get call analytics grouped by property."""
    query = db.query(PhoneCall).filter(
        PhoneCall.agent_id == current_agent.id,
        PhoneCall.property_id.isnot(None)
    )

    if property_id:
        query = query.filter(PhoneCall.property_id == property_id)

    calls = query.all()

    # Group by property
    property_stats = {}
    for call in calls:
        pid = call.property_id
        if pid not in property_stats:
            prop = db.query(Property).filter(Property.id == pid).first()
            property_stats[pid] = {
                "property_id": pid,
                "address": prop.address if prop else "Unknown",
                "total_calls": 0,
                "inbound_calls": 0,
                "outbound_calls": 0,
                "unique_callers": set(),
                "viewings_scheduled": 0,
                "offers_created": 0
            }

        stats = property_stats[pid]
        stats["total_calls"] += 1
        if call.direction == "inbound":
            stats["inbound_calls"] += 1
        else:
            stats["outbound_calls"] += 1

        if call.phone_number:
            stats["unique_callers"].add(call.phone_number)

        if call.outcome == "viewing_scheduled":
            stats["viewings_scheduled"] += 1
        elif call.outcome == "offer_created":
            stats["offers_created"] += 1

    # Convert sets to counts and sort
    for pid in property_stats:
        property_stats[pid]["unique_callers"] = len(property_stats[pid]["unique_callers"])

    sorted_stats = sorted(
        property_stats.values(),
        key=lambda x: x["total_calls"],
        reverse=True
    )[:limit]

    return {"properties": sorted_stats}
