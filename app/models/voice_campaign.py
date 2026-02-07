from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class VoiceCampaign(Base):
    __tablename__ = "voice_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="draft", index=True)
    call_purpose = Column(String(64), nullable=False, default="property_update")

    # Optional default targeting hints.
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True, index=True)
    contact_roles = Column(JSON, nullable=True)

    max_attempts = Column(Integer, nullable=False, default=3)
    retry_delay_minutes = Column(Integer, nullable=False, default=60)
    rate_limit_per_minute = Column(Integer, nullable=False, default=5)

    assistant_overrides = Column(JSON, nullable=True)

    last_run_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    property = relationship("Property")
    targets = relationship(
        "VoiceCampaignTarget",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )


class VoiceCampaignTarget(Base):
    __tablename__ = "voice_campaign_targets"
    __table_args__ = (
        UniqueConstraint("campaign_id", "phone_number", name="uq_campaign_target_phone"),
    )

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("voice_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)

    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True, index=True)

    contact_name = Column(String(255), nullable=True)
    phone_number = Column(String(32), nullable=False)

    status = Column(String(32), nullable=False, default="queued", index=True)
    attempts_made = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)

    last_call_id = Column(String(128), nullable=True, index=True)
    last_call_status = Column(String(64), nullable=True)
    last_disposition = Column(String(64), nullable=True)
    last_error = Column(Text, nullable=True)
    last_webhook_payload = Column(JSON, nullable=True)

    enrolled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    campaign = relationship("VoiceCampaign", back_populates="targets")
    contact = relationship("Contact")
    property = relationship("Property")
