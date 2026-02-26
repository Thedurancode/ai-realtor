"""Phone number model for managing inbound/outbound numbers."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class PhoneNumber(Base):
    """Phone numbers managed by the platform."""

    __tablename__ = "phone_numbers"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Phone number details
    phone_number = Column(String, unique=True, nullable=False, index=True)  # E.164 format: +14155551234
    friendly_name = Column(String, nullable=True)  # e.g., "Main Line", "Listings Hotline"
    provider = Column(String, nullable=False, default="vapi")  # vapi, twilio, plivo
    provider_phone_id = Column(String, nullable=True)  # Provider's phone ID

    # Capabilities
    can_receive_calls = Column(Boolean, default=True)
    can_make_calls = Column(Boolean, default=True)
    can_receive_sms = Column(Boolean, default=False)
    can_send_sms = Column(Boolean, default=False)

    # Configuration
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)  # Primary number for agent
    greeting_message = Column(Text, nullable=True)  # Custom greeting: "Thanks for calling Emprezario"
    ai_voice_id = Column(String, nullable=True)  # ElevenLabs voice ID or VAPI voice
    ai_assistant_id = Column(String, nullable=True)  # VAPI assistant ID

    # Routing
    forward_to_number = Column(String, nullable=True)  # Forward calls to this number
    forward_when = Column(String, nullable=True)  # always, unavailable, after_hours, never
    business_hours_start = Column(String, nullable=True)  # HH:MM format
    business_hours_end = Column(String, nullable=True)  # HH:MM format
    timezone = Column(String, nullable=True, default="America/New_York")

    # Tracking
    total_calls = Column(Integer, default=0)
    total_minutes = Column(Integer, default=0)
    total_cost = Column(Integer, default=0)  # Cents

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_call_at = Column(DateTime, nullable=True)

    # Relationships
    # agent = relationship("Agent", back_populates="phone_numbers")  # Temporarily disabled

    def __repr__(self):
        return f"<PhoneNumber(id={self.id}, number={self.phone_number}, is_primary={self.is_primary})>"
