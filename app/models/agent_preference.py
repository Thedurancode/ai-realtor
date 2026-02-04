from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AgentPreference(Base):
    """
    Store agent-specific preferences, business rules, and context for the AI assistant.
    Examples:
    - "We don't do properties in Florida"
    - "Always contact lawyers before inspectors"
    - "Our business hours are 9-5 EST"
    - "Preferred lender: John Smith at ABC Bank"
    """
    __tablename__ = "agent_preferences"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Preference details
    key = Column(String, nullable=False, index=True)  # e.g., "excluded_states", "business_hours"
    value = Column(Text, nullable=False)  # The actual preference value
    description = Column(Text, nullable=True)  # Human-readable description
    is_active = Column(Boolean, default=True)  # Can temporarily disable preferences

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    agent = relationship("Agent", back_populates="preferences")
