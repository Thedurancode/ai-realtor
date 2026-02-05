"""
Activity router for logging and retrieving activity events
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json

from app.database import get_db
from app.models.activity_event import ActivityEvent, ActivityEventType, ActivityEventStatus


router = APIRouter(prefix="/activities", tags=["activities"])


# Helper function to get WebSocket manager
def get_ws_manager():
    """Get WebSocket manager from main module"""
    try:
        import sys
        if 'app.main' in sys.modules:
            return sys.modules['app.main'].manager
    except:
        pass
    return None


class ActivityEventCreate(BaseModel):
    """Create activity event request"""
    tool_name: str
    user_source: Optional[str] = "Unknown"
    event_type: str = "tool_call"
    status: str = "pending"
    metadata: Optional[dict] = None


class ActivityEventUpdate(BaseModel):
    """Update activity event request"""
    status: Optional[str] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None


class ActivityEventResponse(BaseModel):
    """Activity event response"""
    id: int
    timestamp: datetime
    tool_name: str
    user_source: Optional[str]
    event_type: str
    status: str
    metadata: Optional[str]
    duration_ms: Optional[int]
    error_message: Optional[str]

    class Config:
        from_attributes = True


@router.post("/log", response_model=ActivityEventResponse)
async def log_activity_event(
    activity: ActivityEventCreate,
    db: Session = Depends(get_db)
):
    """
    Log a new activity event (used by MCP server and middleware)
    """
    try:
        event_type = ActivityEventType[activity.event_type.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {activity.event_type}")

    try:
        status = ActivityEventStatus[activity.status.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {activity.status}")

    # Create activity event
    new_event = ActivityEvent(
        tool_name=activity.tool_name,
        user_source=activity.user_source,
        event_type=event_type,
        status=status,
        data=json.dumps(activity.metadata) if activity.metadata else None
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    # Broadcast via WebSocket
    manager = get_ws_manager()
    if manager:
        await manager.broadcast({
            "type": "activity_logged",
            "activity": {
                "id": new_event.id,
                "timestamp": new_event.timestamp.isoformat(),
                "tool_name": new_event.tool_name,
                "user_source": new_event.user_source,
                "event_type": new_event.event_type.value,
                "status": new_event.status.value,
                "metadata": json.loads(new_event.data) if new_event.data else None
            }
        })

    return ActivityEventResponse(
        id=new_event.id,
        timestamp=new_event.timestamp,
        tool_name=new_event.tool_name,
        user_source=new_event.user_source,
        event_type=new_event.event_type.value,
        status=new_event.status.value,
        metadata=new_event.data,
        duration_ms=new_event.duration_ms,
        error_message=new_event.error_message
    )


@router.patch("/{activity_id}", response_model=ActivityEventResponse)
async def update_activity_event(
    activity_id: int,
    update: ActivityEventUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an activity event (typically to update status and duration after completion)
    """
    event = db.query(ActivityEvent).filter(ActivityEvent.id == activity_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Activity event not found")

    # Update fields
    if update.status:
        try:
            event.status = ActivityEventStatus[update.status.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {update.status}")

    if update.duration_ms is not None:
        event.duration_ms = update.duration_ms

    if update.error_message is not None:
        event.error_message = update.error_message

    db.commit()
    db.refresh(event)

    # Broadcast update via WebSocket
    manager = get_ws_manager()
    if manager:
        event_type = "tool_completed" if event.status == ActivityEventStatus.SUCCESS else "tool_failed"
        await manager.broadcast({
            "type": event_type,
            "activity": {
                "id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "tool_name": event.tool_name,
                "user_source": event.user_source,
                "event_type": event.event_type.value,
                "status": event.status.value,
                "duration_ms": event.duration_ms,
                "error_message": event.error_message,
                "metadata": json.loads(event.data) if event.data else None
            }
        })

    return ActivityEventResponse(
        id=event.id,
        timestamp=event.timestamp,
        tool_name=event.tool_name,
        user_source=event.user_source,
        event_type=event.event_type.value,
        status=event.status.value,
        metadata=event.data,
        duration_ms=event.duration_ms,
        error_message=event.error_message
    )


@router.get("/recent", response_model=List[ActivityEventResponse])
def get_recent_activities(
    limit: int = 50,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get recent activity events

    Args:
        limit: Maximum number of events to return (default: 50)
        event_type: Filter by event type (optional)
        status: Filter by status (optional)
    """
    query = db.query(ActivityEvent)

    # Apply filters
    if event_type:
        try:
            event_type_enum = ActivityEventType[event_type.upper()]
            query = query.filter(ActivityEvent.event_type == event_type_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")

    if status:
        try:
            status_enum = ActivityEventStatus[status.upper()]
            query = query.filter(ActivityEvent.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    # Order by timestamp descending and apply limit
    events = query.order_by(ActivityEvent.timestamp.desc()).limit(limit).all()

    return [
        ActivityEventResponse(
            id=e.id,
            timestamp=e.timestamp,
            tool_name=e.tool_name,
            user_source=e.user_source,
            event_type=e.event_type.value,
            status=e.status.value,
            metadata=e.data,
            duration_ms=e.duration_ms,
            error_message=e.error_message
        )
        for e in events
    ]


@router.delete("/{activity_id}")
def delete_activity_event(
    activity_id: int,
    db: Session = Depends(get_db)
):
    """Delete an activity event"""
    event = db.query(ActivityEvent).filter(ActivityEvent.id == activity_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Activity event not found")

    db.delete(event)
    db.commit()
    return {"status": "deleted", "activity_id": activity_id}
