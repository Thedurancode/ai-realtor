"""Phone call model for inbound/outbound voice interactions."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class PhoneCall(Base):
    """Record of phone calls (inbound and outbound)."""

    __tablename__ = "phone_calls"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)

    # Call details
    direction = Column(String, nullable=False)  # 'inbound' or 'outbound'
    phone_number = Column(String, nullable=False)  # Caller ID (for inbound) or destination (for outbound)
    provider = Column(String, nullable=False, default="vapi")  # 'vapi', 'telnyx', 'elevenlabs'
    vapi_call_id = Column(String, unique=True, nullable=True)  # VAPI call UUID
    telnyx_call_id = Column(String, unique=True, nullable=True)  # Telnyx call control ID
    telnyx_call_session_id = Column(String, nullable=True)  # Telnyx session ID
    telnyx_call_leg_id = Column(String, nullable=True)  # Telnyx leg ID
    vapi_phone_number_id = Column(String, nullable=True)  # VAPI phone number ID

    # Call status
    status = Column(String, nullable=False, default="initiated")  # initiated, in_progress, completed, failed, no_answer, busy
    duration_seconds = Column(Integer, nullable=True)  # Call duration
    cost = Column(Float, nullable=True)  # Call cost in USD

    # AI interaction
    transcription = Column(Text, nullable=True)  # Full call transcript
    summary = Column(Text, nullable=True)  # AI-generated summary
    intent = Column(String, nullable=True)  # Detected intent: property_inquiry, schedule_viewing, offer, speak_agent, general
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)  # Property discussed
    confidence_score = Column(Float, nullable=True)  # AI confidence in intent (0-1)

    # Outcome
    outcome = Column(String, nullable=True)  # information_provided, viewing_scheduled, offer_created, message_taken, transferred
    caller_name = Column(String, nullable=True)  # If caller provided name
    caller_phone = Column(String, nullable=True)  # Verified caller phone
    message = Column(Text, nullable=True)  # Message left for agent
    follow_up_created = Column(Boolean, default=False)  # Was follow-up task created?

    # Recording
    recording_url = Column(String, nullable=True)  # VAPI recording URL
    recording_transcribed = Column(Boolean, default=False)  # Was transcription processed?

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    # agent = relationship("Agent", back_populates="phone_calls")  # Temporarily disabled
    property = relationship("Property", back_populates="phone_calls")

    def __repr__(self):
        return f"<PhoneCall(id={self.id}, direction={self.direction}, status={self.status}, phone={self.phone_number})>"
