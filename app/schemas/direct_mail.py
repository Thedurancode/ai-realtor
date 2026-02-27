"""Pydantic Schemas for Direct Mail API"""

from pydantic import BaseModel, Field, HttpUrl, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MailType(str, Enum):
    POSTCARD = "postcard"
    LETTER = "letter"
    CHECK = "check"


class MailStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    MAILED = "mailed"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"


class PostcardSize(str, Enum):
    SIZE_4X6 = "4x6"
    SIZE_6X9 = "6x9"
    SIZE_6X11 = "6x11"


class LetterSize(str, Enum):
    LETTER = "letter"
    LEGAL = "legal"
    A4 = "a4"


# Address Schema
class AddressSchema(BaseModel):
    """US Postal Address"""
    name: str = Field(..., description="Recipient name")
    company: Optional[str] = Field(None, description="Company name")
    address_line1: str = Field(..., description="Street address")
    address_line2: Optional[str] = Field(None, description="Apartment, suite, etc.")
    address_city: str = Field(..., description="City")
    address_state: str = Field(..., description="State (2-letter code)")
    address_zip: str = Field(..., description="ZIP code")
    address_country: str = Field(default="US", description="Country code (2-letter)")


# Create Schemas
class DirectMailBase(BaseModel):
    """Base fields for direct mail"""
    mail_type: MailType
    campaign_name: Optional[str] = None
    campaign_type: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PostcardCreate(DirectMailBase):
    """Create a new postcard"""
    mail_type: MailType = Field(default=MailType.POSTCARD, const=True)
    to_address: AddressSchema
    from_address: Optional[AddressSchema] = None  # Uses agent's default if not provided
    front_html: str = Field(..., description="HTML for front of postcard")
    back_html: Optional[str] = Field(None, description="HTML for back of postcard")
    size: PostcardSize = Field(default=PostcardSize.SIZE_4X6)
    merge_variables: Optional[Dict[str, Any]] = Field(default_factory=dict)
    property_id: Optional[int] = None
    contact_id: Optional[int] = None
    send_after: Optional[datetime] = None
    template_name: Optional[str] = None


class LetterCreate(DirectMailBase):
    """Create a new letter"""
    mail_type: MailType = Field(default=MailType.LETTER, const=True)
    to_address: AddressSchema
    from_address: Optional[AddressSchema] = None
    file_url: str = Field(..., description="URL to PDF file for letter content")
    color: bool = Field(default=False)
    double_sided: bool = Field(default=True)
    certified_mail: bool = Field(default=False)
    return_envelope: bool = Field(default=False)
    size: LetterSize = Field(default=LetterSize.LETTER)
    property_id: Optional[int] = None
    contact_id: Optional[int] = None
    send_after: Optional[datetime] = None


class CheckCreate(DirectMailBase):
    """Create a new check"""
    mail_type: MailType = Field(default=MailType.CHECK, const=True)
    to_address: AddressSchema
    from_address: Optional[AddressSchema] = None
    check_amount: float = Field(..., gt=0, description="Amount of check")
    check_number: Optional[str] = None
    memo: Optional[str] = None
    bank_account: str = Field(..., description="Lob bank account ID")


class BulkPostcardCreate(BaseModel):
    """Create multiple postcards"""
    campaign_name: str
    property_ids: Optional[List[int]] = None
    contact_ids: Optional[List[int]] = None
    filters: Optional[Dict[str, Any]] = None  # Dynamic filters
    template_name: str
    size: PostcardSize = Field(default=PostcardSize.SIZE_4X6)
    color: bool = Field(default=False)
    send_immediately: bool = Field(default=False)
    scheduled_for: Optional[datetime] = None


# Response Schemas
class TrackingEventSchema(BaseModel):
    """Individual tracking event"""
    event_id: str
    status: str
    timestamp: datetime
    location: Optional[str] = None
    description: Optional[str] = None


class DirectMailResponse(BaseModel):
    """Full direct mail response"""
    id: int
    agent_id: int
    property_id: Optional[int] = None
    contact_id: Optional[int] = None
    mail_type: MailType
    mail_status: MailStatus
    lob_mailpiece_id: Optional[str] = None
    to_address: Dict[str, Any]
    from_address: Dict[str, Any]
    template_name: Optional[str] = None
    postcard_size: Optional[PostcardSize] = None
    letter_size: Optional[LetterSize] = None
    color: bool = False
    double_sided: bool = True
    certified_mail: bool = False
    send_after: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    expected_delivery_date: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    tracking_events: Optional[List[TrackingEventSchema]] = None
    tracking_url: Optional[str] = None
    campaign_name: Optional[str] = None
    campaign_type: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DirectMailVoiceSummary(BaseModel):
    """Voice-friendly summary for TTS"""
    id: int
    mail_type: str
    status: str
    recipient: str
    campaign: Optional[str] = None
    sent_date: Optional[str] = None
    delivery_status: Optional[str] = None
    tracking_summary: Optional[str] = None


# Template Schemas
class DirectMailTemplateCreate(BaseModel):
    """Create a new template"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    template_type: str = Field(..., regex="^(postcard|letter)$")
    campaign_type: Optional[str] = None
    front_html_template: str = Field(..., description="HTML template with {{variables}}")
    back_html_template: Optional[str] = None
    default_postcard_size: PostcardSize = Field(default=PostcardSize.SIZE_4X6)
    default_color: bool = Field(default=False)
    default_double_sided: bool = Field(default=True)
    required_variables: List[str] = Field(default_factory=list)
    is_active: bool = Field(default=True)


class DirectMailTemplateResponse(BaseModel):
    """Template response"""
    id: int
    agent_id: int
    name: str
    description: Optional[str] = None
    template_type: str
    campaign_type: Optional[str] = None
    front_html_template: str
    back_html_template: Optional[str] = None
    default_postcard_size: Optional[PostcardSize] = None
    default_color: bool = False
    default_double_sided: bool = True
    required_variables: List[str] = []
    preview_image_url: Optional[str] = None
    is_active: bool = True
    is_system_template: bool = False
    created_at: datetime


# Campaign Schemas
class DirectMailCampaignCreate(BaseModel):
    """Create a bulk campaign"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    campaign_type: Optional[str] = None
    template_id: Optional[int] = None
    target_property_ids: Optional[List[int]] = None
    target_contact_ids: Optional[List[int]] = None
    filters: Optional[Dict[str, Any]] = None
    mail_type: MailType
    postcard_size: PostcardSize = Field(default=PostcardSize.SIZE_4X6)
    color: bool = Field(default=False)
    double_sided: bool = Field(default=True)
    send_immediately: bool = Field(default=False)
    scheduled_for: Optional[datetime] = None


class DirectMailCampaignResponse(BaseModel):
    """Campaign response"""
    id: int
    agent_id: int
    template_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    campaign_type: Optional[str] = None
    mail_type: MailType
    postcard_size: Optional[PostcardSize] = None
    color: bool = False
    double_sided: bool = True
    status: str
    total_recipients: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    failed_count: int = 0
    total_cost: float = 0.0
    scheduled_for: Optional[datetime] = None
    created_at: datetime


# Address Verification Schema
class AddressVerificationRequest(BaseModel):
    """Request to verify an address"""
    address_line1: str
    address_line2: Optional[str] = None
    address_city: str
    address_state: str
    address_zip: str


class AddressVerificationResponse(BaseModel):
    """Verified address"""
    original_address: Dict[str, str]
    verified_address: Dict[str, str]
    is_valid: bool
    deliverability: str  # deliverable, undeliverable, etc.
    lob_verification_id: Optional[str] = None
