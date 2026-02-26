"""
Calendar Integration Models

Connects agents to external calendars (Google Calendar) and syncs
tasks, follow-ups, and appointments.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class CalendarConnection(Base):
    """
    External calendar connection (e.g., Google Calendar)
    """
    __tablename__ = "calendar_connections"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)

    # Calendar provider
    provider = Column(String, nullable=False)  # 'google', 'outlook', 'apple'

    # OAuth tokens (encrypted in production)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Calendar details
    calendar_id = Column(String, nullable=True)  # e.g., 'primary' or calendar email
    calendar_name = Column(String, nullable=True)
    calendar_color = Column(String, nullable=True)  # Hex color for events

    # Sync settings
    sync_enabled = Column(Boolean, default=True)
    sync_tasks = Column(Boolean, default=True)  # Sync scheduled tasks
    sync_follow_ups = Column(Boolean, default=True)  # Sync follow-up reminders
    sync_appointments = Column(Boolean, default=True)  # Sync property appointments
    sync_contracts = Column(Boolean, default=False)  # Sync contract deadlines

    # Last sync info
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String, nullable=True)  # 'success', 'error', 'pending'
    last_sync_error = Column(Text, nullable=True)

    # Auto-create calendar events for these item types
    auto_create_events = Column(Boolean, default=True)
    event_duration_minutes = Column(Integer, default=60)  # Default duration for tasks
    reminder_minutes = Column(Integer, default=15)  # Default reminder before events

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="calendar_connections")
    synced_events = relationship("SyncedCalendarEvent", back_populates="calendar_connection", cascade="all, delete-orphan")


class SyncedCalendarEvent(Base):
    """
    Records of calendar events that have been synced
    """
    __tablename__ = "synced_calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    calendar_connection_id = Column(Integer, ForeignKey("calendar_connections.id"), nullable=False, index=True)

    # What was synced
    source_type = Column(String, nullable=False)  # 'scheduled_task', 'follow_up', 'contract', 'appointment'
    source_id = Column(Integer, nullable=True)  # ID of the source item

    # Calendar event details
    external_event_id = Column(String, nullable=True)  # ID in external calendar
    external_event_link = Column(String, nullable=True)  # Link to view event in calendar

    # Event details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)

    # Timing
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    all_day = Column(Boolean, default=False)

    # Reminders
    reminder_minutes = Column(Integer, nullable=True)

    # Sync status
    sync_status = Column(String, nullable=False)  # 'created', 'updated', 'deleted', 'error'
    sync_error = Column(Text, nullable=True)
    last_synced_at = Column(DateTime, default=datetime.utcnow)

    # Status
    is_active = Column(Boolean, default=True)  # False if event was deleted in source
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    calendar_connection = relationship("CalendarConnection", back_populates="synced_events")


class CalendarEvent(Base):
    """
    Manual calendar events created by agents
    """
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True, index=True)

    # Event details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)

    # Timing
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    all_day = Column(Boolean, default=False)

    # Reminders
    reminder_minutes = Column(Integer, nullable=True)

    # Event type/category
    event_type = Column(String, nullable=True)  # 'showing', 'inspection', 'closing', 'meeting', 'other'
    color = Column(String, nullable=True)  # Hex color for calendar display

    # Attendees (JSON array of {name, email, status})
    attendees = Column(JSON, nullable=True)

    # Status
    status = Column(String, nullable=False, default='confirmed')  # 'confirmed', 'tentative', 'cancelled'

    # Calendar sync
    external_event_id = Column(String, nullable=True)  # If synced to external calendar
    external_calendar_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="calendar_events")
    property = relationship("Property", back_populates="calendar_events")
