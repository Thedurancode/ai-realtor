"""Direct Mail Models for Lob.com Integration"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class MailType(str, enum.Enum):
    """Type of direct mail"""
    POSTCARD = "postcard"
    LETTER = "letter"
    CHECK = "check"


class MailStatus(str, enum.Enum):
    """Status of mailpiece through Lob's system"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    MAILED = "mailed"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"


class PostcardSize(str, enum.Enum):
    """Standard postcard sizes"""
    SIZE_4X6 = "4x6"
    SIZE_6X9 = "6x9"
    SIZE_6X11 = "6x11"


class LetterSize(str, enum.Enum):
    """Standard letter sizes"""
    LETTER = "letter"
    LEGAL = "legal"
    A4 = "a4"


class DirectMail(Base):
    """
    Direct mail campaigns sent via Lob.com
    Tracks postcards, letters, and checks sent to contacts/properties
    """
    __tablename__ = "direct_mail"

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)

    # Mail details
    mail_type = Column(SQLEnum(MailType), nullable=False)
    mail_status = Column(SQLEnum(MailStatus), default=MailStatus.DRAFT, nullable=False)

    # Lob integration
    lob_mailpiece_id = Column(String(100), unique=True, nullable=True)
    lob_object_id = Column(String(100), nullable=True)  # Specific ID for postcard/letter/check

    # Addresses (stored as JSON for flexibility)
    to_address = Column(JSON, nullable=False)
    from_address = Column(JSON, nullable=False)

    # Content
    template_name = Column(String(100))
    front_html = Column(Text)
    back_html = Column(Text)
    file_url = Column(String(1000))  # For letters (PDF URL)
    merge_variables = Column(JSON)  # Personalization data

    # Mail options
    postcard_size = Column(SQLEnum(PostcardSize))
    letter_size = Column(SQLEnum(LetterSize))
    color = Column(Boolean, default=False)
    double_sided = Column(Boolean, default=True)
    certified_mail = Column(Boolean, default=False)
    return_envelope = Column(Boolean, default=False)

    # Scheduling
    send_after = Column(DateTime(timezone=True), nullable=True)  # Future date to send

    # Pricing
    estimated_cost = Column(Float)
    actual_cost = Column(Float)

    # Tracking
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    tracking_events = Column(JSON)  # Array of tracking events
    tracking_url = Column(String(1000))  # Lob tracking URL

    # Campaign metadata
    campaign_name = Column(String(200))
    campaign_type = Column(String(50))  # just_sold, open_house, market_update, etc.
    description = Column(Text)
    metadata = Column(JSON)  # Additional campaign data

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate="now()")

    # Relationships
    agent = relationship("Agent", back_populates="direct_mail_campaigns")
    property = relationship("Property", back_populates="direct_mail_campaigns")
    contact = relationship("Contact", back_populates="direct_mail_received")


class DirectMailTemplate(Base):
    """
    Reusable templates for direct mail campaigns
    """
    __tablename__ = "direct_mail_templates"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Template details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    template_type = Column(String(50), nullable=False)  # postcard, letter
    campaign_type = Column(String(50))  # just_sold, open_house, market_update

    # Content
    front_html_template = Column(Text, nullable=False)
    back_html_template = Column(Text)
    pdf_url_template = Column(String(1000))  # For letters

    # Configuration
    default_postcard_size = Column(SQLEnum(PostcardSize), default=PostcardSize.SIZE_4X6)
    default_color = Column(Boolean, default=False)
    default_double_sided = Column(Boolean, default=True)

    # Required variables for template
    required_variables = Column(JSON)  # ["property_address", "agent_name", etc.]

    # Preview
    preview_image_url = Column(String(1000))

    # Status
    is_active = Column(Boolean, default=True)
    is_system_template = Column(Boolean, default=False)  # Pre-built templates

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate="now()")

    # Relationship
    agent = relationship("Agent")


class DirectMailCampaign(Base):
    """
    Bulk direct mail campaigns targeting multiple recipients
    """
    __tablename__ = "direct_mail_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("direct_mail_templates.id"), nullable=True)

    # Campaign details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    campaign_type = Column(String(50))

    # Targeting
    target_property_ids = Column(JSON)  # Specific properties to target
    target_contact_ids = Column(JSON)  # Specific contacts to target
    filters = Column(JSON)  # Dynamic filters (city, price range, etc.)

    # Configuration
    mail_type = Column(SQLEnum(MailType), nullable=False)
    postcard_size = Column(SQLEnum(PostcardSize), default=PostcardSize.SIZE_4X6)
    color = Column(Boolean, default=False)
    double_sided = Column(Boolean, default=True)

    # Scheduling
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    send_immediately = Column(Boolean, default=False)

    # Stats
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)

    # Status
    status = Column(String(50), default="draft")  # draft, scheduled, sending, completed, cancelled

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate="now()")

    # Relationship
    agent = relationship("Agent")
    template = relationship("DirectMailTemplate")
    contact_lists = relationship("ContactList", back_populates="campaign")
