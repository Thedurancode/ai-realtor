from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ContractStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class RequirementSource(str, enum.Enum):
    """Source of contract requirement"""
    AUTO_ATTACHED = "auto_attached"  # Auto-attached by template rules
    MANUAL = "manual"  # Manually selected by user
    AI_SUGGESTED = "ai_suggested"  # Suggested by AI analysis


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # DocuSeal integration fields
    docuseal_template_id = Column(String, nullable=True)
    docuseal_submission_id = Column(String, nullable=True)
    docuseal_url = Column(String, nullable=True)

    status = Column(Enum(ContractStatus), default=ContractStatus.DRAFT)

    # Requirement fields
    is_required = Column(Boolean, default=True)  # Is this contract required for this property?
    required_by_date = Column(DateTime(timezone=True), nullable=True)  # Optional deadline
    requirement_source = Column(Enum(RequirementSource), default=RequirementSource.AUTO_ATTACHED)
    requirement_reason = Column(Text, nullable=True)  # AI explanation or user note

    # Tracking
    sent_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    property = relationship("Property", back_populates="contracts")
    contact = relationship("Contact", back_populates="contracts")
    submitters = relationship("ContractSubmitter", back_populates="contract", cascade="all, delete-orphan")
