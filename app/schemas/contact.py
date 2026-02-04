from pydantic import BaseModel
from datetime import datetime

from app.models.contact import ContactRole


class ContactBase(BaseModel):
    name: str
    role: ContactRole
    phone: str | None = None
    email: str | None = None
    company: str | None = None
    notes: str | None = None


class ContactCreate(ContactBase):
    property_id: int


class ContactUpdate(BaseModel):
    name: str | None = None
    role: ContactRole | None = None
    phone: str | None = None
    email: str | None = None
    company: str | None = None
    notes: str | None = None


class ContactResponse(ContactBase):
    id: int
    property_id: int
    first_name: str | None = None
    last_name: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ContactCreateFromVoice(BaseModel):
    """
    Voice-optimized contact creation.
    Example: "add a lawyer to this property, his name is Ed Duran, 201-335-5555"
    """

    address_query: str  # Partial address to find property
    role: str  # "lawyer", "contractor", etc. - will be parsed
    name: str  # Full name - will be split into first/last
    phone: str | None = None
    email: str | None = None
    company: str | None = None
    notes: str | None = None


class ContactCreateFromVoiceResponse(BaseModel):
    """Voice-optimized response after creating contact"""

    contact: ContactResponse
    voice_confirmation: str


class ContactListVoiceResponse(BaseModel):
    """Voice-optimized response for listing contacts"""

    contacts: list[ContactResponse]
    voice_summary: str
