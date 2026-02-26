"""Pydantic schemas for phone calls."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PhoneCallResponse(BaseModel):
    """Schema for phone call response."""
    id: int
    agent_id: int
    direction: str  # 'inbound' or 'outbound'
    phone_number: str
    vapi_call_id: Optional[str]
    vapi_phone_number_id: Optional[str]
    status: str
    duration_seconds: Optional[int]
    cost: Optional[float]
    transcription: Optional[str]
    summary: Optional[str]
    intent: Optional[str]
    property_id: Optional[int]
    confidence_score: Optional[float]
    outcome: Optional[str]
    caller_name: Optional[str]
    caller_phone: Optional[str]
    message: Optional[str]
    follow_up_created: bool
    recording_url: Optional[str]
    recording_transcribed: bool
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


class PhoneCallListResponse(BaseModel):
    """Schema for list of phone calls."""
    calls: List[PhoneCallResponse]
    total: int
    limit: int
    offset: int
