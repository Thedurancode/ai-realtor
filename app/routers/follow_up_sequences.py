"""Follow-Up Sequences API — create, manage, and process auto-drip campaigns."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from fastapi import Query

from app.database import get_db
from app.models.follow_up_sequence import SequenceStatus, LeadTemperature
from app.services.follow_up_sequence_service import follow_up_sequence_service
from app.services.follow_up_queue_service import follow_up_queue_service

router = APIRouter(prefix="/sequences", tags=["Follow-Up Sequences"])


class CreateSequenceRequest(BaseModel):
    lead_name: str
    lead_email: Optional[str] = None
    lead_phone: Optional[str] = None
    lead_source: Optional[str] = None
    template_name: str = "default"
    temperature: str = "warm"  # hot, warm, cold
    property_id: Optional[int] = None
    contact_id: Optional[int] = None
    custom_context: Optional[str] = None


class EngagementEvent(BaseModel):
    event: str  # email_opened, email_replied, sms_replied, call_answered, call_voicemail


@router.post("/create")
async def create_sequence(req: CreateSequenceRequest, db: Session = Depends(get_db)):
    """Create a new auto follow-up sequence for a lead."""
    temp_map = {"hot": LeadTemperature.HOT, "warm": LeadTemperature.WARM, "cold": LeadTemperature.COLD}
    temperature = temp_map.get(req.temperature, LeadTemperature.WARM)

    seq = follow_up_sequence_service.create_sequence(
        db, lead_name=req.lead_name, lead_email=req.lead_email,
        lead_phone=req.lead_phone, lead_source=req.lead_source,
        template_name=req.template_name, property_id=req.property_id,
        contact_id=req.contact_id, temperature=temperature,
        custom_context=req.custom_context,
    )
    return {"message": f"Sequence created for {req.lead_name}", "id": seq.id, "steps": seq.total_steps}


@router.post("/process")
async def process_due_touches(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Process all due touches across all active sequences."""
    due = follow_up_sequence_service.get_due_count(db)
    if due == 0:
        return {"message": "No touches due", "processed": 0}

    results = follow_up_sequence_service.process_due_touches(db)
    return {"message": f"Processed {len(results)} touches", "results": results}


@router.get("/list")
async def list_sequences(
    status: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List all follow-up sequences."""
    seq_status = None
    if status:
        try:
            seq_status = SequenceStatus(status)
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    return follow_up_sequence_service.list_sequences(db, status=seq_status, limit=limit)


@router.get("/{sequence_id}")
async def get_sequence(sequence_id: int, db: Session = Depends(get_db)):
    """Get sequence details with all touches."""
    seq = follow_up_sequence_service.get_sequence(db, sequence_id)
    if not seq:
        raise HTTPException(404, "Sequence not found")
    return seq


@router.post("/{sequence_id}/pause")
async def pause_sequence(sequence_id: int, db: Session = Depends(get_db)):
    return follow_up_sequence_service.pause_sequence(db, sequence_id)


@router.post("/{sequence_id}/resume")
async def resume_sequence(sequence_id: int, db: Session = Depends(get_db)):
    return follow_up_sequence_service.resume_sequence(db, sequence_id)


@router.post("/{sequence_id}/cancel")
async def cancel_sequence(sequence_id: int, db: Session = Depends(get_db)):
    return follow_up_sequence_service.cancel_sequence(db, sequence_id)


@router.post("/{sequence_id}/engagement")
async def record_engagement(sequence_id: int, event: EngagementEvent, db: Session = Depends(get_db)):
    """Record an engagement event (email opened, reply received, etc.)."""
    return follow_up_sequence_service.record_engagement(db, sequence_id, event.event)


@router.get("/templates/list")
async def list_templates():
    """List all available sequence templates."""
    return follow_up_sequence_service.get_templates()


# ── Follow-Up Queue (merged from follow_ups.py) ─────────────────

class CompleteBody(BaseModel):
    note: Optional[str] = None


class SnoozeBody(BaseModel):
    hours: int = 72


_queue_router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])


@_queue_router.get("/queue")
def get_follow_up_queue(
    limit: int = Query(10, description="Max items to return (1-25)", ge=1, le=25),
    priority: Optional[str] = Query(None, description="Filter: urgent, high, medium, low"),
    db: Session = Depends(get_db),
):
    return follow_up_queue_service.get_queue(db, limit=limit, priority=priority)


@_queue_router.post("/{property_id}/complete")
def complete_follow_up(property_id: int, body: CompleteBody = CompleteBody(), db: Session = Depends(get_db)):
    return follow_up_queue_service.complete_follow_up(db, property_id, note=body.note)


@_queue_router.post("/{property_id}/snooze")
def snooze_follow_up(property_id: int, body: SnoozeBody = SnoozeBody(), db: Session = Depends(get_db)):
    return follow_up_queue_service.snooze_follow_up(db, property_id, hours=body.hours)
