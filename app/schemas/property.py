from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.models.property import PropertyStatus, PropertyType, DealType


class PropertyBase(BaseModel):
    title: str
    description: str | None = None
    address: str
    city: str
    state: str
    zip_code: str
    price: float
    bedrooms: int | None = None
    bathrooms: float | None = None
    square_feet: int | None = None
    lot_size: float | None = None
    year_built: int | None = None
    property_type: PropertyType = PropertyType.HOUSE
    status: PropertyStatus = PropertyStatus.AVAILABLE
    deal_type: DealType | None = None


class PropertyCreate(PropertyBase):
    agent_id: int


class PropertyCreateFromVoice(BaseModel):
    """Voice-optimized property creation using place_id for address"""

    place_id: str  # Google Places ID from autocomplete
    agent_id: int
    title: str | None = None  # Auto-generated if not provided
    description: str | None = None
    price: float
    bedrooms: int | None = None
    bathrooms: float | None = None
    square_feet: int | None = None
    lot_size: float | None = None
    year_built: int | None = None
    property_type: PropertyType = PropertyType.HOUSE
    status: PropertyStatus = PropertyStatus.AVAILABLE
    deal_type: DealType | None = None


class PropertyCreateFromVoiceResponse(BaseModel):
    """Response with voice confirmation after creating property"""

    property: "PropertyResponse"
    voice_confirmation: str  # Text for voice agent to speak


class PropertyUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    price: float | None = None
    bedrooms: int | None = None
    bathrooms: float | None = None
    square_feet: int | None = None
    lot_size: float | None = None
    year_built: int | None = None
    property_type: PropertyType | None = None
    status: PropertyStatus | None = None
    deal_type: DealType | None = None
    agent_id: int | None = None


class SkipTraceResponse(BaseModel):
    """Skip trace data for property owner"""
    id: int
    property_id: int
    owner_name: Optional[str] = None
    owner_first_name: Optional[str] = None
    owner_last_name: Optional[str] = None
    phone_numbers: List[Dict[str, Any]] = []
    emails: List[Dict[str, Any]] = []
    mailing_address: Optional[str] = None
    mailing_city: Optional[str] = None
    mailing_state: Optional[str] = None
    mailing_zip: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ZillowEnrichmentResponse(BaseModel):
    """Zillow enrichment data for property"""
    id: int
    property_id: int
    zpid: Optional[int] = None
    zestimate: Optional[float] = None
    zestimate_low: Optional[float] = None
    zestimate_high: Optional[float] = None
    rent_zestimate: Optional[float] = None
    living_area: Optional[float] = None
    lot_size: Optional[float] = None
    lot_area_units: Optional[str] = None
    year_built: Optional[int] = None
    home_type: Optional[str] = None
    home_status: Optional[str] = None
    days_on_zillow: Optional[int] = None
    page_view_count: Optional[int] = None
    favorite_count: Optional[int] = None
    property_tax_rate: Optional[float] = None
    annual_tax_amount: Optional[float] = None
    hdp_url: Optional[str] = None
    zillow_url: Optional[str] = None
    photos: Optional[List[str]] = None
    description: Optional[str] = None
    schools: Optional[List[Dict[str, Any]]] = None
    tax_history: Optional[List[Dict[str, Any]]] = None
    price_history: Optional[List[Dict[str, Any]]] = None
    reso_facts: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PropertyResponse(PropertyBase):
    id: int
    agent_id: int
    created_at: datetime
    updated_at: datetime | None = None
    zillow_enrichment: Optional[ZillowEnrichmentResponse] = None
    skip_traces: List[SkipTraceResponse] = []

    class Config:
        from_attributes = True
