"""
Calendar Integration API Routes

Endpoints for:
- Google Calendar OAuth flow
- Calendar connection management
- Calendar event management
- Sync operations
"""
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from datetime import datetime, timedelta
from typing import Optional, List

from app.database import SessionLocal
from app.models.calendar_integration import CalendarConnection, SyncedCalendarEvent, CalendarEvent
from app.models.scheduled_task import ScheduledTask
from app.services.calendar_service import GoogleCalendarService, CalendarSyncService

router = APIRouter(prefix="/calendar", tags=["calendar"])


# ─── Dependencies ───

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_agent_id(request: Request) -> int:
    """Get agent_id from request state (set by auth middleware)"""
    agent_id = getattr(request.state, "agent_id", None)
    if not agent_id:
        raise HTTPException(status_code=401, detail="Agent authentication required")
    return agent_id


# ─── Schemas ───

class CalendarAuthUrlResponse(BaseModel):
    auth_url: str
    state: str


class CalendarConnectionResponse(BaseModel):
    id: int
    provider: str
    calendar_id: Optional[str]
    calendar_name: Optional[str]
    sync_enabled: bool
    is_active: bool
    created_at: datetime


class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    reminder_minutes: Optional[int] = 15
    event_type: Optional[str] = None
    color: Optional[str] = None
    property_id: Optional[int] = None
    create_meet: bool = False
    attendees: Optional[List[dict]] = None


class CalendarEventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    location: Optional[str]
    start_time: datetime
    end_time: datetime
    all_day: bool
    reminder_minutes: Optional[int]
    event_type: Optional[str]
    status: str
    external_event_id: Optional[str]
    meet_link: Optional[str] = None
    attendees: Optional[List[dict]] = None
    color: Optional[str] = None
    property_address: Optional[str] = None
    property_id: Optional[int] = None


class SyncResponse(BaseModel):
    synced: int
    skipped: int
    errors: List[str]


# ─── OAuth Flow ───

@router.get("/auth/url", response_model=CalendarAuthUrlResponse)
def get_calendar_auth_url(
    agent_id: int = Depends(get_agent_id),
    db: Session = Depends(get_db)
):
    """
    Get Google Calendar OAuth authorization URL

    Returns URL for user to visit and authorize access
    """
    import secrets
    from datetime import datetime, timedelta

    # Generate state token (CSRF protection + agent_id + timestamp)
    state_token = f"{agent_id}:{secrets.token_urlsafe(16)}:{int(datetime.utcnow().timestamp())}"

    # Get redirect URI from environment or use default
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/calendar/callback")

    auth_url = GoogleCalendarService.get_auth_url(redirect_uri, state_token)

    return CalendarAuthUrlResponse(
        auth_url=auth_url,
        state=state_token
    )


@router.post("/callback")
async def calendar_oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback from Google

    Exchange authorization code for tokens and save connection
    """
    # Parse state token
    try:
        parts = state.split(":")
        if len(parts) != 3:
            raise ValueError("Invalid state token")

        agent_id = int(parts[0])
        timestamp = int(parts[2])

        # Verify timestamp is within 10 minutes
        if datetime.utcnow().timestamp() - timestamp > 600:
            raise HTTPException(status_code=400, detail="State token expired")

    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid state token: {str(e)}")

    # Exchange code for tokens
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/calendar/callback")
    tokens = await GoogleCalendarService.exchange_code_for_tokens(code, redirect_uri)

    # Get user's calendar list
    calendars = await GoogleCalendarService.list_calendars(tokens["access_token"])

    # Create or update calendar connection
    connection = db.query(CalendarConnection).filter(
        CalendarConnection.agent_id == agent_id,
        CalendarConnection.provider == "google",
        CalendarConnection.is_active == True
    ).first()

    if connection:
        # Update existing connection
        connection.access_token = tokens["access_token"]
        connection.refresh_token = tokens.get("refresh_token")
        connection.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))

        # Update calendar info
        if calendars:
            primary_cal = [c for c in calendars if c.get("id") == "primary"]
            if primary_cal:
                connection.calendar_id = primary_cal[0]["id"]
                connection.calendar_name = primary_cal[0].get("summary", "Primary Calendar")
    else:
        # Create new connection
        connection = CalendarConnection(
            agent_id=agent_id,
            provider="google",
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            token_expires_at=datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600)),
            calendar_id=calendars[0]["id"] if calendars else "primary",
            calendar_name=calendars[0].get("summary", "Google Calendar") if calendars else "Primary Calendar",
            is_active=True,
        )
        db.add(connection)

    db.commit()

    # Redirect to frontend success page
    return {
        "message": "Calendar connected successfully!",
        "calendar_name": connection.calendar_name,
        "redirect_to": "/settings/calendar"
    }


# ─── Calendar Connections ───

@router.get("/connections", response_model=List[CalendarConnectionResponse])
def list_calendar_connections(
    agent_id: int = Depends(get_agent_id),
    db: Session = Depends(get_db)
):
    """List all calendar connections for the agent"""
    connections = db.query(CalendarConnection).filter(
        CalendarConnection.agent_id == agent_id
    ).all()
    return connections


@router.get("/connections/{connection_id}", response_model=CalendarConnectionResponse)
def get_calendar_connection(
    connection_id: int,
    agent_id: int = Depends(get_agent_id),
    db: Session = Depends(get_db)
):
    """Get a specific calendar connection"""
    connection = db.query(CalendarConnection).filter(
        CalendarConnection.id == connection_id,
        CalendarConnection.agent_id == agent_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Calendar connection not found")

    return connection


@router.patch("/connections/{connection_id}")
async def update_calendar_connection(
    connection_id: int,
    sync_enabled: Optional[bool] = None,
    sync_tasks: Optional[bool] = None,
    sync_follow_ups: Optional[bool] = None,
    sync_contracts: Optional[bool] = None,
    agent_id: int = Depends(get_agent_id),
    db: Session = Depends(get_db)
):
    """Update calendar connection sync settings"""
    connection = db.query(CalendarConnection).filter(
        CalendarConnection.id == connection_id,
        CalendarConnection.agent_id == agent_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Calendar connection not found")

    if sync_enabled is not None:
        connection.sync_enabled = sync_enabled
    if sync_tasks is not None:
        connection.sync_tasks = sync_tasks
    if sync_follow_ups is not None:
        connection.sync_follow_ups = sync_follow_ups
    if sync_contracts is not None:
        connection.sync_contracts = sync_contracts

    db.commit()

    return {"message": "Calendar connection updated"}


@router.delete("/connections/{connection_id}")
def delete_calendar_connection(
    connection_id: int,
    agent_id: int = Depends(get_agent_id),
    db: Session = Depends(get_db)
):
    """Delete a calendar connection"""
    connection = db.query(CalendarConnection).filter(
        CalendarConnection.id == connection_id,
        CalendarConnection.agent_id == agent_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Calendar connection not found")

    db.delete(connection)
    db.commit()

    return {"message": "Calendar connection deleted"}


# ── Calendar Events ───

@router.get("/events", response_model=List[CalendarEventResponse])
def list_calendar_events(
    agent_id: int = Depends(get_agent_id),
    property_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_type: Optional[str] = None,
    days: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List calendar events with enriched data

    Query parameters:
    - days: Number of days ahead to look (default: 7)
    - property_id: Filter by property
    - event_type: Filter by event type (showing, inspection, closing, meeting, other)
    - start_date: Filter by start date
    - end_date: Filter by end date
    """
    from app.models.property import Property

    query = db.query(CalendarEvent).filter(CalendarEvent.agent_id == agent_id)

    # If days specified, calculate start_date from now
    if days:
        from datetime import timedelta
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days)
        query = query.filter(CalendarEvent.start_time >= start_date)
        query = query.filter(CalendarEvent.start_time <= end_date)

    if property_id:
        query = query.filter(CalendarEvent.property_id == property_id)

    if start_date and not days:
        query = query.filter(CalendarEvent.start_time >= start_date)

    if end_date and not days:
        query = query.filter(CalendarEvent.end_time <= end_date)

    if event_type:
        query = query.filter(CalendarEvent.event_type == event_type)

    db_events = query.order_by(CalendarEvent.start_time).all()

    # Enrich events with additional data
    events = []
    for event in db_events:
        event_dict = {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "location": event.location,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "all_day": event.all_day,
            "reminder_minutes": event.reminder_minutes,
            "event_type": event.event_type,
            "status": event.status,
            "external_event_id": event.external_event_id,
            "meet_link": None,
            "attendees": event.attendees,
            "color": event.color,
            "property_id": event.property_id,
            "property_address": None,
        }

        # Add property address if linked
        if event.property_id:
            prop = db.query(Property).filter(Property.id == event.property_id).first()
            if prop:
                event_dict["property_address"] = f"{prop.address}, {prop.city}"

        # Add meet link if we can extract it from synced events
        if event.external_event_id:
            synced = db.query(SyncedCalendarEvent).filter(
                SyncedCalendarEvent.source_type == "manual_event",
                SyncedCalendarEvent.source_id == event.id,
                SyncedCalendarEvent.external_event_id == event.external_event_id
            ).first()
            if synced and synced.external_event_link:
                event_dict["meet_link"] = synced.external_event_link

        events.append(CalendarEventResponse(**event_dict))

    return events


@router.post("/events", response_model=CalendarEventResponse)
async def create_calendar_event(
    event: CalendarEventCreate,
    agent_id: int = Depends(get_agent_id),
    db: Session = Depends(get_db)
):
    """Create a manual calendar event with optional Google Meet link"""
    # Extract fields that aren't in the database model
    event_dict = event.dict()
    create_meet = event_dict.pop("create_meet", False)
    attendees = event_dict.pop("attendees", None)

    db_event = CalendarEvent(
        agent_id=agent_id,
        **event_dict
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    # Auto-sync to connected calendars if enabled
    connections = db.query(CalendarConnection).filter(
        CalendarConnection.agent_id == agent_id,
        CalendarConnection.is_active == True,
        CalendarConnection.auto_create_events == True
    ).all()

    meet_link = None
    for connection in connections:
        sync_service = CalendarSyncService(db)
        try:
            result = await sync_service.sync_calendar_event(
                db_event,
                connection,
                create_meet=create_meet,
                attendees=attendees
            )
            if result and result.get("meet_link"):
                meet_link = result["meet_link"]
                db_event.external_event_id = result.get("external_event_id")
        except Exception as e:
            # Log but don't fail the event creation
            print(f"Failed to sync event to calendar: {e}")

    db.commit()

    # Build enriched response
    from app.models.property import Property

    response_data = {
        "id": db_event.id,
        "title": db_event.title,
        "description": db_event.description,
        "location": db_event.location,
        "start_time": db_event.start_time,
        "end_time": db_event.end_time,
        "all_day": db_event.all_day,
        "reminder_minutes": db_event.reminder_minutes,
        "event_type": db_event.event_type,
        "status": db_event.status,
        "external_event_id": db_event.external_event_id,
        "meet_link": meet_link,
        "attendees": attendees,
        "color": db_event.color,
        "property_id": db_event.property_id,
        "property_address": None,
    }

    # Add property address if linked
    if db_event.property_id:
        prop = db.query(Property).filter(Property.id == db_event.property_id).first()
        if prop:
            response_data["property_address"] = f"{prop.address}, {prop.city}"

    return CalendarEventResponse(**response_data)


@router.get("/events/{event_id}", response_model=CalendarEventResponse)
def get_calendar_event(
    event_id: int,
    agent_id: int = Depends(get_agent_id),
    db: Session = Depends(get_db)
):
    """Get a specific calendar event with enriched data"""
    from app.models.property import Property

    event = db.query(CalendarEvent).filter(
        CalendarEvent.id == event_id,
        CalendarEvent.agent_id == agent_id
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail="Calendar event not found")

    # Build enriched response
    event_dict = {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "location": event.location,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "all_day": event.all_day,
        "reminder_minutes": event.reminder_minutes,
        "event_type": event.event_type,
        "status": event.status,
        "external_event_id": event.external_event_id,
        "meet_link": None,
        "attendees": event.attendees,
        "color": event.color,
        "property_id": event.property_id,
        "property_address": None,
    }

    # Add property address if linked
    if event.property_id:
        prop = db.query(Property).filter(Property.id == event.property_id).first()
        if prop:
            event_dict["property_address"] = f"{prop.address}, {prop.city}"

    # Add meet link if we can extract it from synced events
    if event.external_event_id:
        synced = db.query(SyncedCalendarEvent).filter(
            SyncedCalendarEvent.source_type == "manual_event",
            SyncedCalendarEvent.source_id == event.id,
            SyncedCalendarEvent.external_event_id == event.external_event_id
        ).first()
        if synced and synced.external_event_link:
            event_dict["meet_link"] = synced.external_event_link

    return CalendarEventResponse(**event_dict)


@router.patch("/events/{event_id}")
def update_calendar_event(
    event_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    reminder_minutes: Optional[int] = None,
    status: Optional[str] = None,
    agent_id: int = Depends(get_agent_id),
    db: Session = Depends(get_db)
):
    """Update a calendar event"""
    event = db.query(CalendarEvent).filter(
        CalendarEvent.id == event_id,
        CalendarEvent.agent_id == agent_id
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail="Calendar event not found")

    if title is not None:
        event.title = title
    if description is not None:
        event.description = description
    if location is not None:
        event.location = location
    if start_time is not None:
        event.start_time = start_time
    if end_time is not None:
        event.end_time = end_time
    if reminder_minutes is not None:
        event.reminder_minutes = reminder_minutes
    if status is not None:
        event.status = status

    db.commit()
    db.refresh(event)

    return event


@router.delete("/events/{event_id}")
def delete_calendar_event(
    event_id: int,
    agent_id: int = Depends(get_agent_id),
    db: Session = Depends(get_db)
):
    """Delete a calendar event"""
    event = db.query(CalendarEvent).filter(
        CalendarEvent.id == event_id,
        CalendarEvent.agent_id == agent_id
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail="Calendar event not found")

    # Also delete from external calendar if synced
    if event.external_event_id:
        connections = db.query(CalendarConnection).filter(
            CalendarConnection.agent_id == agent_id
        ).all()
        for connection in connections:
            if connection.calendar_id == event.external_calendar_id:
                import asyncio
                try:
                    asyncio.create_task(
                        GoogleCalendarService.delete_event(
                            access_token=connection.access_token,
                            calendar_id=connection.calendar_id or "primary",
                            event_id=event.external_event_id
                        )
                    )
                except Exception:
                    pass  # Log but don't fail

    db.delete(event)
    db.commit()

    return {"message": "Calendar event deleted"}


# ── Sync Operations ───

@router.post("/sync/{connection_id}", response_model=SyncResponse)
async def sync_to_calendar(
    connection_id: int,
    agent_id: int = Depends(get_agent_id),
    db: Session = Depends(get_db)
):
    """
    Manually trigger sync of all pending items to calendar

    Syncs scheduled tasks, follow-ups, etc. based on connection settings
    """
    connection = db.query(CalendarConnection).filter(
        CalendarConnection.id == connection_id,
        CalendarConnection.agent_id == agent_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Calendar connection not found")

    # Check if token needs refresh
    if connection.token_expires_at and connection.token_expires_at < datetime.utcnow():
        try:
            tokens = await GoogleCalendarService.refresh_access_token(connection.refresh_token)
            connection.access_token = tokens["access_token"]
            if "refresh_token" in tokens:
                connection.refresh_token = tokens["refresh_token"]
            connection.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
            db.commit()
        except Exception as e:
            connection.last_sync_status = "error"
            connection.last_sync_error = str(e)
            db.commit()
            raise HTTPException(status_code=400, detail=f"Failed to refresh access token: {str(e)}")

    # Perform sync
    sync_service = CalendarSyncService(db)

    try:
        sync_result = await sync_service.sync_all_pending_items(connection)
    except Exception as e:
        connection.last_sync_status = "error"
        connection.last_sync_error = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

    return SyncResponse(
        synced=sync_result["synced"],
        skipped=sync_result["skipped"],
        errors=sync_result["errors"]
    )


@router.get("/synced-events/{connection_id}")
def list_synced_events(
    connection_id: int,
    agent_id: int = Depends(get_agent_id),
    db: Session = Depends(get_db)
):
    """List all synced events for a calendar connection"""
    # Verify ownership
    connection = db.query(CalendarConnection).filter(
        CalendarConnection.id == connection_id,
        CalendarConnection.agent_id == agent_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Calendar connection not found")

    events = db.query(SyncedCalendarEvent).filter(
        SyncedCalendarEvent.calendar_connection_id == connection_id,
        SyncedCalendarEvent.is_active == True
    ).order_by(SyncedCalendarEvent.start_time).all()

    return events
