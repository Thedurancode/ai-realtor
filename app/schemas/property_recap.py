from pydantic import BaseModel
from typing import Optional


class RecapResponse(BaseModel):
    """Property recap response"""
    id: int
    property_id: int
    property_address: str
    recap_text: str
    voice_summary: str
    recap_context: dict
    version: int
    last_trigger: Optional[str]

    class Config:
        from_attributes = True


class PhoneCallRequest(BaseModel):
    """Phone call request"""
    phone_number: str  # E.164 format (e.g., +14155551234)
    call_purpose: Optional[str] = "property_update"
    custom_context: Optional[dict] = None


class PhoneCallResponse(BaseModel):
    """Phone call response"""
    success: bool
    call_id: str
    status: str
    property_id: int
    property_address: str
    phone_number: str
    call_purpose: str
    message: str
