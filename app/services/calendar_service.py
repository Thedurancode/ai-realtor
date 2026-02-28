"""
Google Calendar Integration Service

Handles OAuth flow and calendar sync operations.
"""
import os
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.calendar_integration import CalendarConnection, SyncedCalendarEvent, CalendarEvent
from app.models.scheduled_task import ScheduledTask
from app.models.property import Property

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Service for Google Calendar integration"""

    # Google OAuth endpoints
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"

    # Required scopes
    SCOPES = [
        "https://www.googleapis.com/auth/calendar.events",  # Create/edit events
    ]

    @staticmethod
    def get_auth_url(redirect_uri: str, state: str) -> str:
        """
        Generate Google OAuth authorization URL

        Args:
            redirect_uri: Where to redirect after authorization
            state: CSRF protection token

        Returns:
            Authorization URL
        """
        client_id = os.getenv("GOOGLE_CLIENT_ID")

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(GoogleCalendarService.SCOPES),
            "response_type": "code",
            "access_type": "offline",  # Get refresh token
            "state": state,
            "prompt": "consent",  # Force consent to get refresh token
        }

        url = f"{GoogleCalendarService.AUTH_URL}?{urlencode(params)}"
        return url

    @staticmethod
    async def exchange_code_for_tokens(code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange OAuth code for access and refresh tokens

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: Must match the redirect_uri used in auth URL

        Returns:
            Dictionary with access_token, refresh_token, expires_in
        """
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                GoogleCalendarService.TOKEN_URL,
                data=data
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token

        Args:
            refresh_token: Refresh token from previous auth

        Returns:
            Dictionary with access_token, expires_in, refresh_token
        """
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        data = {
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GoogleCalendarService.TOKEN_URL,
                data=data
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def is_token_expired(connection: CalendarConnection, buffer_minutes: int = 5) -> bool:
        """
        Check if a calendar connection's access token is expired or will expire soon.

        Args:
            connection: Calendar connection with token_expires_at field
            buffer_minutes: Buffer time in minutes to refresh token before actual expiry

        Returns:
            True if token is expired or will expire within buffer time
        """
        if not connection.token_expires_at:
            return True  # No expiry info, assume expired

        now = datetime.utcnow()
        expiry_time = connection.token_expires_at - timedelta(minutes=buffer_minutes)
        return now >= expiry_time

    @staticmethod
    async def get_valid_access_token(db: Session, connection: CalendarConnection) -> str:
        """
        Get a valid access token, refreshing if necessary.

        This helper method checks if the token is expired and automatically refreshes it.
        Updates the CalendarConnection record in the database with the new token.

        Args:
            db: Database session
            connection: Calendar connection with tokens

        Returns:
            Valid access token

        Raises:
            ValueError: If refresh fails (no refresh token available)
        """
        # Check if token is still valid
        if not GoogleCalendarService.is_token_expired(connection):
            return connection.access_token

        # Token is expired, need to refresh
        if not connection.refresh_token:
            logger.error(f"Calendar connection {connection.id} has no refresh token")
            raise ValueError(
                "Calendar access token expired and no refresh token available. "
                "Please re-connect your calendar."
            )

        try:
            logger.info(f"Refreshing access token for calendar connection {connection.id}")
            token_data = await GoogleCalendarService.refresh_access_token(connection.refresh_token)

            # Update connection with new tokens
            connection.access_token = token_data.get("access_token")
            connection.token_expires_at = datetime.utcnow() + timedelta(
                seconds=token_data.get("expires_in", 3600)
            )

            # Google sometimes returns a new refresh token
            if "refresh_token" in token_data:
                connection.refresh_token = token_data["refresh_token"]

            db.commit()
            logger.info(f"Successfully refreshed token for calendar connection {connection.id}")

            return connection.access_token

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to refresh token for calendar connection {connection.id}: {e}")
            raise ValueError(f"Failed to refresh calendar token: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error refreshing token for calendar connection {connection.id}: {e}")
            raise ValueError(f"Failed to refresh calendar token: {str(e)}")

    @staticmethod
    def get_calendar_list_url() -> str:
        """Get URL to list user's calendars"""
        return f"{GoogleCalendarService.CALENDAR_API_BASE}/users/me/calendarList"

    @staticmethod
    async def list_calendars(access_token: str) -> List[Dict[str, Any]]:
        """
        List all calendars for the authenticated user

        Args:
            access_token: Valid Google access token

        Returns:
            List of calendars with id, summary, description, etc.
        """
        url = GoogleCalendarService.get_calendar_list_url()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])

    @staticmethod
    async def create_event(
        access_token: str,
        calendar_id: str,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        location: Optional[str] = None,
        reminder_minutes: Optional[int] = None,
        create_meet: bool = False,
        attendees: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Create an event in Google Calendar

        Args:
            access_token: Valid Google access token
            calendar_id: Calendar ID (usually 'primary' or email)
            title: Event title
            description: Event description
            start_time: Event start time
            end_time: Event end time
            location: Optional location
            reminder_minutes: Optional reminder in minutes before event
            create_meet: If True, creates a Google Meet conference for this event
            attendees: Optional list of attendees (each dict with 'email' key)

        Returns:
            Created event data from Google Calendar API (includes meet link if created)
        """
        url = f"{GoogleCalendarService.CALENDAR_API_BASE}/calendars/{calendar_id}/events"

        # Format times for Google Calendar API (RFC3339)
        start_str = start_time.isoformat()
        end_str = end_time.isoformat()

        event_data = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_str},
            "end": {"dateTime": end_str},
        }

        if location:
            event_data["location"] = location

        # Add Google Meet conference if requested
        if create_meet:
            import uuid
            event_data["conferenceData"] = {
                "createRequest": {
                    "requestId": str(uuid.uuid4()),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}
                }
            }

        # Add attendees if provided
        if attendees:
            event_data["attendees"] = [{"email": a["email"]} for a in attendees]

        if reminder_minutes is not None:
            event_data["reminders"] = {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": reminder_minutes}
                ]
            }

        # Build query parameters
        params = {}
        if create_meet:
            params["conferenceDataVersion"] = "1"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=event_data,
                params=params,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def update_event(
        access_token: str,
        calendar_id: str,
        event_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Update an existing event"""
        url = f"{GoogleCalendarService.CALENDAR_API_BASE}/calendars/{calendar_id}/events/{event_id}"

        event_data = {}
        if title:
            event_data["summary"] = title
        if description:
            event_data["description"] = description

        if start_time and end_time:
            event_data["start"] = {"dateTime": start_time.isoformat()}
            event_data["end"] = {"dateTime": end_time.isoformat()}

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                json=event_data,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def delete_event(access_token: str, calendar_id: str, event_id: str) -> bool:
        """Delete an event"""
        url = f"{GoogleCalendarService.CALENDAR_API_BASE}/calendars/{calendar_id}/events/{event_id}"

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            return response.status_code == 204


def urlencode(params: Dict[str, str]) -> str:
    """Simple URL encoder (since we may not have urllib imported everywhere)"""
    from urllib.parse import urlencode
    return urlencode(params)


class CalendarSyncService:
    """Service for syncing data to external calendars"""

    def __init__(self, db: Session):
        self.db = db

    async def sync_scheduled_task(
        self,
        task: ScheduledTask,
        connection: CalendarConnection
    ) -> Optional[SyncedCalendarEvent]:
        """
        Sync a scheduled task to external calendar

        Args:
            task: Scheduled task to sync
            connection: Calendar connection to sync to

        Returns:
            SyncedCalendarEvent record, or None if sync disabled
        """
        if not connection.sync_tasks or not connection.sync_enabled:
            return None

        # Get valid access token (auto-refreshes if expired)
        access_token = await GoogleCalendarService.get_valid_access_token(self.db, connection)

        # Check if already synced
        existing = self.db.query(SyncedCalendarEvent).filter(
            SyncedCalendarEvent.source_type == "scheduled_task",
            SyncedCalendarEvent.source_id == task.id,
            SyncedCalendarEvent.calendar_connection_id == connection.id,
            SyncedCalendarEvent.is_active == True
        ).first()

        # Calculate event times
        start_time = task.scheduled_at
        duration = timedelta(minutes=connection.event_duration_minutes)
        end_time = start_time + duration

        # Build event details
        property_info = ""
        if task.property_id:
            prop = self.db.query(Property).filter(Property.id == task.property_id).first()
            if prop:
                property_info = f"\n\nProperty: {prop.address}, {prop.city}, {prop.state}"

        title = task.title
        description = (task.description or "") + property_info
        if task.repeat_interval_hours:
            description += f"\n\nRecurring: Every {task.repeat_interval_hours} hours"

        # Sync to Google Calendar
        if existing:
            # Update existing event
            await GoogleCalendarService.update_event(
                access_token=access_token,
                calendar_id=connection.calendar_id or "primary",
                event_id=existing.external_event_id,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
            )
            existing.title = title
            existing.description = description
            existing.start_time = start_time
            existing.end_time = end_time
            existing.last_synced_at = datetime.utcnow()
            self.db.commit()
            return existing
        else:
            # Create new event
            event = await GoogleCalendarService.create_event(
                access_token=access_token,
                calendar_id=connection.calendar_id or "primary",
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                reminder_minutes=connection.reminder_minutes,
            )

            # Create synced event record
            synced_event = SyncedCalendarEvent(
                calendar_connection_id=connection.id,
                source_type="scheduled_task",
                source_id=task.id,
                external_event_id=event["id"],
                external_event_link=event.get("htmlLink"),
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                reminder_minutes=connection.reminder_minutes,
                sync_status="created",
            )
            self.db.add(synced_event)
            self.db.commit()
            return synced_event

    async def sync_follow_up(
        self,
        follow_up: "FollowUp",
        connection: CalendarConnection
    ) -> Optional[SyncedCalendarEvent]:
        """
        Sync a follow-up to external calendar

        Args:
            follow_up: Follow-up to sync
            connection: Calendar connection to sync to

        Returns:
            SyncedCalendarEvent record, or None if sync disabled
        """
        if not connection.sync_follow_ups or not connection.sync_enabled:
            return None

        # Get valid access token (auto-refreshes if expired)
        access_token = await GoogleCalendarService.get_valid_access_token(self.db, connection)

        # Check if already synced
        existing = self.db.query(SyncedCalendarEvent).filter(
            SyncedCalendarEvent.source_type == "follow_up",
            SyncedCalendarEvent.source_id == follow_up.id,
            SyncedCalendarEvent.calendar_connection_id == connection.id,
            SyncedCalendarEvent.is_active == True
        ).first()

        # Calculate event times
        start_time = follow_up.scheduled_at
        duration = timedelta(minutes=connection.event_duration_minutes or 30)
        end_time = start_time + duration

        # Build event details
        property_info = ""
        if follow_up.property_id:
            prop = self.db.query(Property).filter(Property.id == follow_up.property_id).first()
            if prop:
                property_info = f"\n\nProperty: {prop.address}, {prop.city}, {prop.state}"

        title = follow_up.title or f"Follow-up: {follow_up.property_id or 'General'}"
        description = (follow_up.notes or "") + property_info

        # Sync to Google Calendar
        if existing:
            # Update existing event
            await GoogleCalendarService.update_event(
                access_token=access_token,
                calendar_id=connection.calendar_id or "primary",
                event_id=existing.external_event_id,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
            )
            existing.title = title
            existing.description = description
            existing.start_time = start_time
            existing.end_time = end_time
            existing.last_synced_at = datetime.utcnow()
            self.db.commit()
            return existing
        else:
            # Create new event
            event = await GoogleCalendarService.create_event(
                access_token=access_token,
                calendar_id=connection.calendar_id or "primary",
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                reminder_minutes=connection.reminder_minutes,
            )

            # Create synced event record
            synced_event = SyncedCalendarEvent(
                calendar_connection_id=connection.id,
                source_type="follow_up",
                source_id=follow_up.id,
                external_event_id=event["id"],
                external_event_link=event.get("htmlLink"),
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                reminder_minutes=connection.reminder_minutes,
                sync_status="created",
            )
            self.db.add(synced_event)
            self.db.commit()
            return synced_event

    async def sync_calendar_event(
        self,
        event: CalendarEvent,
        connection: CalendarConnection,
        create_meet: bool = False,
        attendees: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sync a manual calendar event to external calendar

        Args:
            event: Calendar event to sync
            connection: Calendar connection to sync to
            create_meet: If True, creates a Google Meet conference
            attendees: Optional list of attendees (each dict with 'email' key)

        Returns:
            Dict with external_event_id and meet_link (if created), or None
        """
        if not connection.sync_appointments or not connection.sync_enabled:
            return None

        # Get valid access token (auto-refreshes if expired)
        access_token = await GoogleCalendarService.get_valid_access_token(self.db, connection)

        # Build description
        description = event.description or ""
        if event.property_id:
            prop = self.db.query(Property).filter(Property.id == event.property_id).first()
            if prop:
                description += f"\n\nProperty: {prop.address}, {prop.city}, {prop.state}"

        meet_link = None

        # Sync to Google Calendar
        if event.external_event_id:
            # Update existing
            await GoogleCalendarService.update_event(
                access_token=access_token,
                calendar_id=connection.calendar_id or "primary",
                event_id=event.external_event_id,
                title=event.title,
                description=description,
                start_time=event.start_time,
                end_time=event.end_time,
            )
            sync_status = "updated"
        else:
            # Create new with optional Google Meet
            google_event = await GoogleCalendarService.create_event(
                access_token=access_token,
                calendar_id=connection.calendar_id or "primary",
                title=event.title,
                description=description,
                start_time=event.start_time,
                end_time=event.end_time,
                location=event.location,
                reminder_minutes=event.reminder_minutes,
                create_meet=create_meet,
                attendees=attendees,
            )
            event.external_event_id = google_event["id"]
            event.external_calendar_id = connection.calendar_id or "primary"
            sync_status = "created"

            # Extract meet link if created
            if create_meet and google_event.get("conferenceData"):
                meet_link = google_event["conferenceData"].get("entryPoints", [{}])[0].get("uri")

        # Update sync status in DB
        self.db.commit()

        # Create/update synced event record
        existing = self.db.query(SyncedCalendarEvent).filter(
            SyncedCalendarEvent.source_type == "manual_event",
            SyncedCalendarEvent.source_id == event.id,
            SyncedCalendarEvent.calendar_connection_id == connection.id
        ).first()

        if existing:
            existing.sync_status = sync_status
            existing.last_synced_at = datetime.utcnow()
        else:
            existing = SyncedCalendarEvent(
                calendar_connection_id=connection.id,
                source_type="manual_event",
                source_id=event.id,
                external_event_id=event.external_event_id,
                external_event_link=f"https://calendar.google.com/calendar/event?eid={event.external_event_id}",
                title=event.title,
                description=description,
                location=event.location,
                start_time=event.start_time,
                end_time=event.end_time,
                all_day=event.all_day,
                reminder_minutes=event.reminder_minutes,
                sync_status=sync_status,
                last_synced_at=datetime.utcnow(),
            )
            self.db.add(existing)

        self.db.commit()

        return {
            "external_event_id": event.external_event_id,
            "meet_link": meet_link,
        }

    async def sync_all_pending_items(self, connection: CalendarConnection) -> dict:
        """
        Sync all pending items for a calendar connection

        Args:
            connection: Calendar connection to sync

        Returns:
            Dict with sync statistics (synced, skipped, errors)
        """
        synced_count = 0
        skipped_count = 0
        errors = []

        # Sync scheduled tasks
        if connection.sync_tasks:
            tasks = self.db.query(ScheduledTask).filter(
                ScheduledTask.status == "pending",
                ScheduledTask.scheduled_at > datetime.utcnow()
            ).limit(50).all()

            for task in tasks:
                try:
                    result = await self.sync_scheduled_task(task, connection)
                    if result:
                        synced_count += 1
                    else:
                        skipped_count += 1
                except Exception as e:
                    errors.append(f"Task {task.id}: {str(e)}")

        # Sync follow-ups
        if connection.sync_follow_ups:
            from app.models.follow_up import FollowUp
            follow_ups = self.db.query(FollowUp).filter(
                FollowUp.status == "pending",
                FollowUp.scheduled_at > datetime.utcnow()
            ).limit(50).all()

            for follow_up in follow_ups:
                try:
                    result = await self.sync_follow_up(follow_up, connection)
                    if result:
                        synced_count += 1
                    else:
                        skipped_count += 1
                except Exception as e:
                    errors.append(f"Follow-up {follow_up.id}: {str(e)}")

        # Update last sync info
        connection.last_sync_at = datetime.utcnow()
        connection.last_sync_status = "success"
        connection.last_sync_error = None
        self.db.commit()

        return {
            "synced": synced_count,
            "skipped": skipped_count,
            "errors": errors
        }
