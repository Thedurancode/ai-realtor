"""Follow-Up Queue router — AI-prioritized follow-up queue."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.follow_up_queue_service import follow_up_queue_service

router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])


class CompleteBody(BaseModel):
    note: Optional[str] = None


class SnoozeBody(BaseModel):
    hours: int = 72


@router.get("/queue")
def get_follow_up_queue(
    limit: int = Query(10, description="Max items to return (1-25)", ge=1, le=25),
    priority: Optional[str] = Query(None, description="Filter: urgent, high, medium, low"),
    db: Session = Depends(get_db),
):
    return follow_up_queue_service.get_queue(db, limit=limit, priority=priority)


@router.post("/{property_id}/complete")
def complete_follow_up(
    property_id: int,
    body: CompleteBody = CompleteBody(),
    db: Session = Depends(get_db),
):
    return follow_up_queue_service.complete_follow_up(db, property_id, note=body.note)


@router.post("/{property_id}/snooze")
def snooze_follow_up(
    property_id: int,
    body: SnoozeBody = SnoozeBody(),
    db: Session = Depends(get_db),
):
    return follow_up_queue_service.snooze_follow_up(db, property_id, hours=body.hours)
