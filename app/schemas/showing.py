from datetime import datetime

from pydantic import BaseModel, Field


class ShowingCreate(BaseModel):
    property_id: int
    client_id: int | None = None
    showing_type: str = "in_person"
    scheduled_at: datetime
    duration_minutes: int = 30
    notes: str | None = None
    attendee_name: str | None = None
    attendee_phone: str | None = None
    attendee_email: str | None = None


class ShowingUpdate(BaseModel):
    showing_type: str | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = None
    notes: str | None = None
    feedback: str | None = None
    attendee_name: str | None = None
    attendee_phone: str | None = None
    attendee_email: str | None = None


class ShowingResponse(BaseModel):
    id: int
    property_id: int
    agent_id: int
    client_id: int | None = None
    showing_type: str
    status: str
    scheduled_at: datetime
    duration_minutes: int
    notes: str | None = None
    feedback: str | None = None
    attendee_name: str | None = None
    attendee_phone: str | None = None
    attendee_email: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ShowingCalendarResponse(BaseModel):
    showings: list[ShowingResponse] = Field(default_factory=list)
    total: int = 0
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None
