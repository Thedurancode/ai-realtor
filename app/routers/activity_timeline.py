"""Activity timeline router — unified chronological event feed."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.activity_timeline_service import activity_timeline_service

router = APIRouter(prefix="/activity-timeline", tags=["activity-timeline"])


@router.get("/")
def get_activity_timeline(
    property_id: Optional[int] = Query(None, description="Filter to specific property"),
    event_types: Optional[str] = Query(None, description="Comma-separated: conversation,notification,note,task,contract,enrichment,skip_trace"),
    search: Optional[str] = Query(None, description="Text search across events"),
    start_date: Optional[str] = Query(None, description="ISO format start date"),
    end_date: Optional[str] = Query(None, description="ISO format end date"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get unified activity timeline with optional filters."""
    parsed_types = [t.strip() for t in event_types.split(",")] if event_types else None
    parsed_start = _parse_date(start_date)
    parsed_end = _parse_date(end_date)

    return activity_timeline_service.get_timeline(
        db=db, property_id=property_id, event_types=parsed_types,
        search=search, start_date=parsed_start, end_date=parsed_end,
        limit=limit, offset=offset,
    )


@router.get("/property/{property_id}")
def get_property_timeline(
    property_id: int,
    event_types: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get activity timeline for a specific property."""
    parsed_types = [t.strip() for t in event_types.split(",")] if event_types else None
    return activity_timeline_service.get_timeline(
        db=db, property_id=property_id, event_types=parsed_types,
        search=search, limit=limit, offset=offset,
    )


@router.get("/recent")
def get_recent_activity(
    property_id: Optional[int] = Query(None),
    hours: int = Query(24, ge=1, le=168, description="Look back N hours"),
    db: Session = Depends(get_db),
):
    """Get recent activity in last N hours (default 24h)."""
    start = datetime.now(timezone.utc) - timedelta(hours=hours)
    return activity_timeline_service.get_timeline(
        db=db, property_id=property_id, start_date=start, limit=100,
    )


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
