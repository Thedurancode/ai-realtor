from pydantic import BaseModel
from datetime import datetime


class PhoneNumber(BaseModel):
    number: str
    type: str  # mobile, landline, work, other
    status: str  # valid, invalid, unknown


class Email(BaseModel):
    email: str
    type: str  # personal, work, secondary


class SkipTraceRequest(BaseModel):
    """Request to skip trace by address (voice: 'skip trace 141 throop ave')"""

    address_query: str  # Partial address from voice input


class SkipTraceByPropertyRequest(BaseModel):
    """Request to skip trace an existing property by ID"""

    property_id: int


class SkipTraceResult(BaseModel):
    """Full skip trace result"""

    id: int
    property_id: int
    owner_name: str | None
    owner_first_name: str | None
    owner_last_name: str | None
    phone_numbers: list[PhoneNumber]
    emails: list[Email]
    mailing_address: str | None
    mailing_city: str | None
    mailing_state: str | None
    mailing_zip: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class SkipTraceVoiceResponse(BaseModel):
    """Voice-optimized response for skip trace results"""

    result: SkipTraceResult
    voice_summary: str  # Text for voice agent to speak
    voice_phone_list: str  # Readable phone numbers
    voice_email_list: str  # Readable emails


class SkipTraceSearchResponse(BaseModel):
    """Response when searching for property to skip trace"""

    property_id: int
    address: str
    city: str
    state: str
    voice_confirmation: str  # "Found property at 141 Throop Ave. Running skip trace now."
