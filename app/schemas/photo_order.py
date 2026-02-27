"""
Pydantic schemas for Property Photo Ordering API

Request/response models for creating and managing photo orders.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, computed_field


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime for display"""
    if not dt:
        return None
    return dt.strftime("%b %d, %Y at %I:%M %p")


def format_currency(amount: Optional[float]) -> str:
    """Format currency for display"""
    if amount is None:
        return "N/A"
    return f"${amount:,.2f}"


# =============================================================================
# PHOTO ORDER SCHEMAS
# =============================================================================

class PhotoOrderCreate(BaseModel):
    """Schema for creating a new photo order"""
    property_id: int
    provider: str = "proxypics"
    requested_date: Optional[datetime] = None
    time_slot_preference: Optional[str] = None  # "morning", "afternoon", "flexible"

    # Location (if different from property address)
    shoot_address: Optional[str] = None
    shoot_city: Optional[str] = None
    shoot_state: Optional[str] = None
    shoot_zip: Optional[str] = None
    special_instructions: Optional[str] = None

    # Contact info
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

    # Services
    services: List[Dict[str, Any]] = Field(default_factory=list)
    # Example: [
    #   {"service_type": "hdr_interior", "quantity": 10, "room_name": "Living Room"},
    #   {"service_type": "exterior_day", "quantity": 3}
    # ]
    rooms_count: Optional[int] = None
    square_footage: Optional[int] = None

    @field_validator("provider")
    def validate_provider(cls, v):
        valid_providers = ["proxypics", "boxbrownie", "photoup", "manual"]
        if v not in valid_providers:
            raise ValueError(f"Provider must be one of {valid_providers}")
        return v

    @field_validator("time_slot_preference")
    def validate_time_slot(cls, v):
        if v and v not in ["morning", "afternoon", "flexible"]:
            raise ValueError('time_slot_preference must be "morning", "afternoon", or "flexible"')
        return v


class PhotoOrderUpdate(BaseModel):
    """Schema for updating a photo order"""
    requested_date: Optional[datetime] = None
    time_slot_preference: Optional[str] = None
    special_instructions: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    services: Optional[List[Dict[str, Any]]] = None
    admin_notes: Optional[str] = None


class PhotoOrderSubmit(BaseModel):
    """Schema for submitting an order to the provider"""
    confirm_submit: bool = True
    notes: Optional[str] = None


class PhotoOrderResponse(BaseModel):
    """Schema for photo order response"""
    id: int
    property_id: int
    agent_id: int
    provider: str
    provider_order_id: Optional[str] = None
    order_status: str
    scheduled_at: Optional[datetime] = None
    requested_date: Optional[datetime] = None
    time_slot_preference: Optional[str] = None

    shoot_address: str
    shoot_city: str
    shoot_state: str
    shoot_zip: str
    shoot_lat: Optional[float] = None
    shoot_lng: Optional[float] = None
    special_instructions: Optional[str] = None

    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

    services_requested: Optional[List[Dict[str, Any]]] = None
    rooms_count: Optional[int] = None
    square_footage: Optional[int] = None

    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    currency: str = "USD"

    photographer_assigned: Optional[str] = None
    photographer_phone: Optional[str] = None
    estimated_completion: Optional[datetime] = None

    delivery_url: Optional[str] = None
    delivery_count: int = 0
    delivery_format: Optional[str] = None

    submitted_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    admin_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    # Computed fields for display
    @computed_field
    @property
    def requested_at_formatted(self) -> Optional[str]:
        return format_datetime(self.requested_date)

    @computed_field
    @property
    def scheduled_at_formatted(self) -> Optional[str]:
        return format_datetime(self.scheduled_at)

    @computed_field
    @property
    def estimated_cost_formatted(self) -> str:
        return format_currency(self.estimated_cost)

    @computed_field
    @property
    def actual_cost_formatted(self) -> str:
        return format_currency(self.actual_cost)

    @computed_field
    @property
    def estimated_completion_formatted(self) -> Optional[str]:
        return format_datetime(self.estimated_completion)

    @computed_field
    @property
    def created_at_formatted(self) -> str:
        return format_datetime(self.created_at)

    class Config:
        from_attributes = True


class PhotoOrderSummary(BaseModel):
    """Lightweight schema for order lists"""
    id: int
    property_id: int
    property_address: Optional[str] = None
    provider: str
    order_status: str
    scheduled_at: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    delivery_count: int = 0
    created_at: datetime

    @computed_field
    @property
    def scheduled_at_formatted(self) -> Optional[str]:
        return format_datetime(self.scheduled_at)

    @computed_field
    @property
    def estimated_cost_formatted(self) -> str:
        return format_currency(self.estimated_cost)

    @computed_field
    @property
    def created_at_formatted(self) -> str:
        return format_datetime(self.created_at)

    class Config:
        from_attributes = True


# =============================================================================
# PHOTO ORDER ITEM SCHEMAS
# =============================================================================

class PhotoOrderItemCreate(BaseModel):
    """Schema for adding items to an order"""
    service_type: str
    service_name: str
    description: Optional[str] = None
    quantity: int = 1
    room_name: Optional[str] = None
    floor: Optional[str] = None
    enhancement_options: Optional[Dict[str, Any]] = None
    unit_price: Optional[float] = None


class PhotoOrderItemResponse(BaseModel):
    """Schema for order item response"""
    id: int
    order_id: int
    service_type: str
    service_name: str
    description: Optional[str] = None
    quantity: int = 1
    room_name: Optional[str] = None
    floor: Optional[str] = None
    enhancement_options: Optional[Dict[str, Any]] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    provider_item_id: Optional[str] = None
    status: str = "pending"
    created_at: datetime
    updated_at: Optional[datetime] = None

    @computed_field
    @property
    def unit_price_formatted(self) -> str:
        return format_currency(self.unit_price)

    @computed_field
    @property
    def total_price_formatted(self) -> str:
        return format_currency(self.total_price)

    class Config:
        from_attributes = True


# =============================================================================
# PHOTO ORDER DELIVERABLE SCHEMAS
# =============================================================================

class PhotoOrderDeliverableResponse(BaseModel):
    """Schema for deliverable response"""
    id: int
    order_id: int
    order_item_id: Optional[int] = None
    file_name: str
    file_url: str
    file_type: str
    file_format: str
    file_size_bytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    room_name: Optional[str] = None
    sequence: Optional[int] = None
    thumbnail_url: Optional[str] = None
    preview_url: Optional[str] = None
    original_url: Optional[str] = None
    is_approved: bool = False
    is_featured: bool = False
    processing_status: str = "pending"
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PhotoOrderDeliverableUpdate(BaseModel):
    """Schema for updating deliverable"""
    is_approved: Optional[bool] = None
    is_featured: Optional[bool] = None
    room_name: Optional[str] = None
    sequence: Optional[int] = None


# =============================================================================
# PHOTO ORDER TEMPLATE SCHEMAS
# =============================================================================

class PhotoOrderTemplateCreate(BaseModel):
    """Schema for creating a template"""
    template_name: str
    description: Optional[str] = None
    services: List[Dict[str, Any]]
    base_price: Optional[float] = None
    property_types: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_active: bool = True


class PhotoOrderTemplateResponse(BaseModel):
    """Schema for template response"""
    id: int
    agent_id: int
    template_name: str
    description: Optional[str] = None
    is_active: bool = True
    services: List[Dict[str, Any]]
    base_price: Optional[float] = None
    currency: str = "USD"
    property_types: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @computed_field
    @property
    def base_price_formatted(self) -> str:
        return format_currency(self.base_price)

    @computed_field
    @property
    def created_at_formatted(self) -> str:
        return format_datetime(self.created_at)

    class Config:
        from_attributes = True


# =============================================================================
# VOICE-READY SUMMARIES
# =============================================================================

class PhotoOrderVoiceSummary(BaseModel):
    """Voice-friendly summary of order status"""
    order_id: int
    property_address: str
    status: str
    scheduled_date: Optional[str] = None
    photographer: Optional[str] = None
    services_count: int = 0
    photos_delivered: int = 0
    estimated_cost: Optional[str] = None
    voice_summary: str  # Natural language summary for TTS


class PhotoServiceAvailability(BaseModel):
    """Service availability for a property"""
    property_id: int
    services_available: List[str]
    estimated_costs: Dict[str, float]
    recommended_package: Optional[str] = None
    current_orders: int = 0
    can_order: bool = True
    reason: Optional[str] = None


# =============================================================================
# WEBHOOK SCHEMAS (for provider callbacks)
# =============================================================================

class ProxyPicsWebhookPayload(BaseModel):
    """Schema for ProxyPics webhook payloads"""
    event_type: str  # "order_created", "order_confirmed", "photos_uploaded", "order_completed"
    order_id: str  # External order ID
    internal_order_id: int  # Our database ID
    status: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class BoxBrownieWebhookPayload(BaseModel):
    """Schema for BoxBrownie webhook payloads"""
    order_id: str
    status: str
    download_url: Optional[str] = None
    images: Optional[List[Dict[str, Any]]] = None
