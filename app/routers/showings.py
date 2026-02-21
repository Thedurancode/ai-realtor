from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.showing import Showing, ShowingStatus
from app.schemas.showing import (
    ShowingCalendarResponse,
    ShowingCreate,
    ShowingResponse,
    ShowingUpdate,
)

router = APIRouter(prefix="/showings", tags=["showings"])


@router.post("/", response_model=ShowingResponse, status_code=201)
def create_showing(payload: ShowingCreate, request: Request, db: Session = Depends(get_db)):
    agent_id = getattr(request.state, "agent_id", 1)
    showing = Showing(agent_id=agent_id, **payload.model_dump())
    db.add(showing)
    db.commit()
    db.refresh(showing)
    return ShowingResponse.model_validate(showing)


@router.get("/", response_model=list[ShowingResponse])
def list_showings(
    request: Request,
    property_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    agent_id = getattr(request.state, "agent_id", 1)
    q = db.query(Showing).filter(Showing.agent_id == agent_id)
    if property_id:
        q = q.filter(Showing.property_id == property_id)
    if status:
        q = q.filter(Showing.status == status)
    q = q.order_by(Showing.scheduled_at.desc())
    showings = q.offset(offset).limit(limit).all()
    return [ShowingResponse.model_validate(s) for s in showings]


@router.get("/calendar", response_model=ShowingCalendarResponse)
def get_calendar(
    request: Request,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    agent_id = getattr(request.state, "agent_id", 1)
    q = db.query(Showing).filter(Showing.agent_id == agent_id)
    if start:
        q = q.filter(Showing.scheduled_at >= start)
    if end:
        q = q.filter(Showing.scheduled_at <= end)
    q = q.order_by(Showing.scheduled_at.asc())
    showings = q.all()
    return ShowingCalendarResponse(
        showings=[ShowingResponse.model_validate(s) for s in showings],
        total=len(showings),
        date_range_start=start,
        date_range_end=end,
    )


@router.get("/property/{property_id}", response_model=list[ShowingResponse])
def get_property_showings(property_id: int, db: Session = Depends(get_db)):
    showings = (
        db.query(Showing)
        .filter(Showing.property_id == property_id)
        .order_by(Showing.scheduled_at.desc())
        .all()
    )
    return [ShowingResponse.model_validate(s) for s in showings]


@router.get("/{showing_id}", response_model=ShowingResponse)
def get_showing(showing_id: int, db: Session = Depends(get_db)):
    showing = db.query(Showing).filter(Showing.id == showing_id).first()
    if not showing:
        raise HTTPException(status_code=404, detail="Showing not found")
    return ShowingResponse.model_validate(showing)


@router.patch("/{showing_id}", response_model=ShowingResponse)
def update_showing(showing_id: int, payload: ShowingUpdate, db: Session = Depends(get_db)):
    showing = db.query(Showing).filter(Showing.id == showing_id).first()
    if not showing:
        raise HTTPException(status_code=404, detail="Showing not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(showing, key, value)
    db.commit()
    db.refresh(showing)
    return ShowingResponse.model_validate(showing)


@router.delete("/{showing_id}", status_code=204)
def cancel_showing(showing_id: int, db: Session = Depends(get_db)):
    showing = db.query(Showing).filter(Showing.id == showing_id).first()
    if not showing:
        raise HTTPException(status_code=404, detail="Showing not found")
    showing.status = ShowingStatus.CANCELLED
    db.commit()


@router.post("/{showing_id}/confirm", response_model=ShowingResponse)
def confirm_showing(showing_id: int, db: Session = Depends(get_db)):
    showing = db.query(Showing).filter(Showing.id == showing_id).first()
    if not showing:
        raise HTTPException(status_code=404, detail="Showing not found")
    showing.status = ShowingStatus.CONFIRMED
    db.commit()
    db.refresh(showing)
    return ShowingResponse.model_validate(showing)


@router.post("/{showing_id}/complete", response_model=ShowingResponse)
def complete_showing(showing_id: int, feedback: str | None = None, db: Session = Depends(get_db)):
    showing = db.query(Showing).filter(Showing.id == showing_id).first()
    if not showing:
        raise HTTPException(status_code=404, detail="Showing not found")
    showing.status = ShowingStatus.COMPLETED
    if feedback:
        showing.feedback = feedback
    db.commit()
    db.refresh(showing)
    return ShowingResponse.model_validate(showing)
