"""Pydantic schemas for phone number management."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PhoneNumberBase(BaseModel):
    """Base phone number fields."""
    phone_number: str = Field(..., description="E.164 format: +14155551234")
    friendly_name: Optional[str] = Field(None, description="e.g., Main Line, Listings Hotline")
    provider: str = Field(default="vapi", description="vapi, twilio, plivo")
    provider_phone_id: Optional[str] = Field(None, description="Provider's phone ID")
    can_receive_calls: bool = Field(default=True)
    can_make_calls: bool = Field(default=True)
    can_receive_sms: bool = Field(default=False)
    can_send_sms: bool = Field(default=False)
    is_active: bool = Field(default=True)
    is_primary: bool = Field(default=False)
    greeting_message: Optional[str] = Field(None, description="Custom greeting message")
    ai_voice_id: Optional[str] = Field(None, description="ElevenLabs or VAPI voice ID")
    ai_assistant_id: Optional[str] = Field(None, description="VAPI assistant ID")
    forward_to_number: Optional[str] = Field(None, description="Forward calls to this number")
    forward_when: Optional[str] = Field(None, description="always, unavailable, after_hours, never")
    business_hours_start: Optional[str] = Field(None, description="HH:MM format")
    business_hours_end: Optional[str] = Field(None, description="HH:MM format")
    timezone: str = Field(default="America/New_York")


class PhoneNumberCreate(PhoneNumberBase):
    """Schema for creating a phone number."""
    pass


class PhoneNumberUpdate(BaseModel):
    """Schema for updating a phone number (all fields optional)."""
    friendly_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None
    greeting_message: Optional[str] = None
    ai_voice_id: Optional[str] = None
    ai_assistant_id: Optional[str] = None
    forward_to_number: Optional[str] = None
    forward_when: Optional[str] = None
    business_hours_start: Optional[str] = None
    business_hours_end: Optional[str] = None
    timezone: Optional[str] = None


class PhoneNumberResponse(PhoneNumberBase):
    """Schema for phone number response."""
    id: int
    agent_id: int
    total_calls: int
    total_minutes: int
    total_cost: int  # Cents
    created_at: datetime
    updated_at: datetime
    last_call_at: Optional[datetime]

    class Config:
        from_attributes = True
