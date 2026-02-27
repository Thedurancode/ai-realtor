"""
Property Photo Ordering System

Integrates with ProxyPics API for ordering professional property photography.
Supports multiple photo types, scheduling, and deliverable tracking.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from typing import Optional, List, Dict, Any

from app.database import Base


class PhotoProvider(str, enum.Enum):
    """Supported photography service providers"""
    PROXYPICS = "proxypics"
    BOXBROWNIE = "boxbrownie"
    PHOTOUP = "photoup"
    MANUAL = "manual"  # Photographer arranged outside platform


class PhotoOrderStatus(str, enum.Enum):
    """Order lifecycle states"""
    DRAFT = "draft"  # Order created but not submitted
    PENDING = "pending"  # Submitted to provider, awaiting confirmation
    CONFIRMED = "confirmed"  # Provider confirmed, shoot scheduled
    IN_PROGRESS = "in_progress"  # Photo shoot in progress
    UPLOADING = "uploading"  # Photos being uploaded
    REVIEW = "review"  # Photos ready for review
    COMPLETED = "completed"  # Order complete, all photos delivered
    CANCELLED = "cancelled"  # Order cancelled
    FAILED = "failed"  # Order failed


class PhotoServiceType(str, enum.Enum):
    """Types of photography services available"""
    # Still Photography
    HDR_INTERIOR = "hdr_interior"  # HDR interior shots
    EXTERIOR_DAY = "exterior_day"  # Exterior daytime shots
    EXTERIOR_TWILIGHT = "exterior_twilight"  # Twilight exterior shots
    AERIAL_DRONE = "aerial_drone"  # Aerial/drone photography
    PANORAMIC_360 = "panoramic_360"  # 360° panoramic shots
    VIRTUAL_TOUR_3D = "virtual_tour_3d"  # 3D virtual tour (Matterport-style)

    # Video
    WALKTHROUGH_VIDEO = "walkthrough_video"  # Video walkthrough
    AERIAL_VIDEO = "aerial_video"  # Drone video footage

    # Enhancement Services
    VIRTUAL_STAGING = "virtual_staging"  # Add furniture to empty rooms
    TWILIGHT_CONVERSION = "twilight_conversion"  # Convert day to twilight
    OBJECT_REMOVAL = "object_removal"  # Remove objects from photos
    SKY_REPLACEMENT = "sky_replacement"  # Replace sky
    FLOOR_PLAN = "floor_plan"  # 2D floor plan creation

    # Editing
    BASIC_EDITING = "basic_editing"  # Color correction, exposure
    ADVANCED_EDITING = "advanced_editing"  # Retouching, perspective correction


class PhotoOrder(Base):
    """
    Property photography order

    Tracks order from creation through delivery.
    Integrates with ProxyPics or similar services.
    """
    __tablename__ = "photo_orders"
    __table_args__ = (
        Index("ix_photo_orders_property_id", "property_id"),
        Index("ix_photo_orders_agent_id", "agent_id"),
        Index("ix_photo_orders_status", "order_status"),
        Index("ix_photo_orders_provider", "provider"),
        Index("ix_photo_orders_scheduled_at", "scheduled_at"),
        Index("ix_photo_orders_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Provider information
    provider = Column(Enum(PhotoProvider), default=PhotoProvider.PROXYPICS, nullable=False)
    provider_order_id = Column(String(100), nullable=True)  # External order ID from provider

    # Order status
    order_status = Column(Enum(PhotoOrderStatus, values_callable=lambda x: [e.value for e in x]),
                         default=PhotoOrderStatus.DRAFT, nullable=False)

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    requested_date = Column(DateTime(timezone=True), nullable=True)  # Agent's preferred date
    time_slot_preference = Column(String(100), nullable=True)  # "morning", "afternoon", "flexible"

    # Address & location
    shoot_address = Column(String(500), nullable=False)
    shoot_city = Column(String(100), nullable=False)
    shoot_state = Column(String(50), nullable=False)
    shoot_zip = Column(String(20), nullable=False)
    shoot_lat = Column(Float, nullable=True)  # GPS coordinates
    shoot_lng = Column(Float, nullable=True)
    special_instructions = Column(Text, nullable=True)  # Gate codes, pet info, etc.

    # Contact info
    contact_name = Column(String(200), nullable=True)  # On-site contact
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(200), nullable=True)

    # Services requested
    services_requested = Column(JSON, nullable=True)  # List of PhotoServiceType
    rooms_count = Column(Integer, nullable=True)  # Number of rooms to photograph
    square_footage = Column(Integer, nullable=True)

    # Pricing
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    currency = Column(String(3), default="USD")

    # Provider responses
    provider_response = Column(JSON, nullable=True)  # Raw provider API response
    photographer_assigned = Column(String(200), nullable=True)  # Photographer name
    photographer_phone = Column(String(50), nullable=True)
    estimated_completion = Column(DateTime(timezone=True), nullable=True)

    # Delivery
    delivery_url = Column(String(1000), nullable=True)  # Link to download photos
    delivery_count = Column(Integer, default=0)  # Number of photos delivered
    delivery_format = Column(String(50), nullable=True)  # "jpg", "png", etc.

    # Tracking
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Notes
    admin_notes = Column(Text, nullable=True)  # Internal notes
    cancellation_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    items = relationship("PhotoOrderItem", back_populates="order", cascade="all, delete-orphan")
    deliverables = relationship("PhotoOrderDeliverable", back_populates="order", cascade="all, delete-orphan")


class PhotoOrderItem(Base):
    """
    Individual service/item within a photo order

    Each item represents a specific type of photo or service requested.
    """
    __tablename__ = "photo_order_items"
    __table_args__ = (
        Index("ix_photo_order_items_order_id", "order_id"),
        Index("ix_photo_order_items_service_type", "service_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("photo_orders.id"), nullable=False)

    # Service details
    service_type = Column(Enum(PhotoServiceType), nullable=False)
    service_name = Column(String(200), nullable=False)  # Display name
    description = Column(Text, nullable=True)

    # Quantity & specifications
    quantity = Column(Integer, default=1)  # Number of photos/shots
    room_name = Column(String(200), nullable=True)  # For room-specific shots
    floor = Column(String(50), nullable=True)  # "ground floor", "second floor", etc.

    # Enhancement options
    enhancement_options = Column(JSON, nullable=True)  # Specific edits requested
    # Example: {"sky_replacement": true, "object_removal": ["cars", "debris"]}

    # Pricing
    unit_price = Column(Float, nullable=True)
    total_price = Column(Float, nullable=True)

    # Status tracking
    provider_item_id = Column(String(100), nullable=True)  # External item ID
    status = Column(String(50), default="pending")  # pending, in_progress, completed, failed

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    order = relationship("PhotoOrder", back_populates="items")


class PhotoOrderDeliverable(Base):
    """
    Individual photo/file delivered for an order

    Tracks each delivered photo, video, or file.
    """
    __tablename__ = "photo_order_deliverables"
    __table_args__ = (
        Index("ix_photo_order_deliverables_order_id", "order_id"),
        Index("ix_photo_order_deliverables_item_id", "order_item_id"),
        Index("ix_photo_order_deliverables_type", "file_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("photo_orders.id"), nullable=False)
    order_item_id = Column(Integer, ForeignKey("photo_order_items.id"), nullable=True)

    # File information
    file_name = Column(String(500), nullable=False)
    file_url = Column(String(1000), nullable=False)  # Cloud storage URL
    file_type = Column(String(50), nullable=False)  # "photo", "video", "floor_plan", "tour"
    file_format = Column(String(20), nullable=False)  # "jpg", "png", "mp4", etc.
    file_size_bytes = Column(Integer, nullable=True)

    # Image metadata (for photos)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    room_name = Column(String(200), nullable=True)  # Which room this photo shows
    sequence = Column(Integer, nullable=True)  # Order in gallery

    # Thumbnails/versions
    thumbnail_url = Column(String(1000), nullable=True)
    preview_url = Column(String(1000), nullable=True)  # Mid-resolution preview
    original_url = Column(String(1000), nullable=True)  # Full-resolution original

    # Processing status
    is_approved = Column(Boolean, default=False)  # Agent approved
    is_featured = Column(Boolean, default=False)  # Mark as primary listing photo
    processing_status = Column(String(50), default="pending")  # pending, processing, ready, failed

    # Provider metadata
    provider_file_id = Column(String(200), nullable=True)  # External file ID
    provider_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    order = relationship("PhotoOrder", back_populates="deliverables")


class PhotoOrderTemplate(Base):
    """
    Reusable photo order templates

    Pre-configured service packages for common scenarios.
    """
    __tablename__ = "photo_order_templates"
    __table_args__ = (
        Index("ix_photo_order_templates_agent_id", "agent_id"),
        Index("ix_photo_order_templates_is_active", "is_active"),
    )

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Template details
    template_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Services included
    services = Column(JSON, nullable=False)  # List of service configurations
    # Example: [
    #   {"service_type": "hdr_interior", "quantity": 10, "unit_price": 15},
    #   {"service_type": "exterior_day", "quantity": 3, "unit_price": 10}
    # ]

    # Pricing
    base_price = Column(Float, nullable=True)
    currency = Column(String(3), default="USD")

    # Property type applicability
    property_types = Column(JSON, nullable=True)  # Which property types this applies to
    # Example: ["HOUSE", "CONDO"]

    # Metadata
    tags = Column(JSON, nullable=True)  # ["basic", "premium", "luxury", "quick"]

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
