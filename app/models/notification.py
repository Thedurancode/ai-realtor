"""
Notification model for real-time alerts
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum


class NotificationType(enum.Enum):
    """Types of notifications"""
    CONTRACT_SIGNED = "contract_signed"
    NEW_LEAD = "new_lead"
    PROPERTY_PRICE_CHANGE = "property_price_change"
    PROPERTY_STATUS_CHANGE = "property_status_change"
    APPOINTMENT_REMINDER = "appointment_reminder"
    SKIP_TRACE_COMPLETE = "skip_trace_complete"
    ENRICHMENT_COMPLETE = "enrichment_complete"
    GENERAL = "general"


class NotificationPriority(enum.Enum):
    """Priority levels for notifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.MEDIUM)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Optional references
    property_id = Column(Integer, nullable=True)
    contact_id = Column(Integer, nullable=True)
    contract_id = Column(Integer, nullable=True)
    agent_id = Column(Integer, nullable=True)

    # Metadata
    data = Column(Text, nullable=True)  # JSON string for extra data
    icon = Column(String(50), nullable=True)  # Icon name or emoji
    action_url = Column(String(500), nullable=True)  # Link to related resource

    # Status
    is_read = Column(Boolean, default=False, index=True)
    is_dismissed = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)

    # Auto-dismiss after X seconds (for TV display)
    auto_dismiss_seconds = Column(Integer, nullable=True)
