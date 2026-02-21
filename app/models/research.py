"""
Research Model

Tracks research jobs and their results.
"""
from sqlalchemy import Column, Index, Integer, String, DateTime, ForeignKey, Enum, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ResearchStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchType(str, enum.Enum):
    """Types of research that can be performed"""
    PROPERTY_ANALYSIS = "property_analysis"  # Complete property research
    MARKET_ANALYSIS = "market_analysis"  # Market trends and comparables
    COMPLIANCE_CHECK = "compliance_check"  # Legal compliance research
    CONTRACT_ANALYSIS = "contract_analysis"  # Contract requirements research
    OWNER_RESEARCH = "owner_research"  # Skip trace and owner info
    NEIGHBORHOOD_ANALYSIS = "neighborhood_analysis"  # Area research
    CUSTOM = "custom"  # Custom research with specified endpoints
    AI_RESEARCH = "ai_research"  # Custom AI prompts with specified models
    API_RESEARCH = "api_research"  # Custom API calls to external services


class Research(Base):
    """
    Research job that can trigger multiple endpoint calls and aggregate results.

    Example use cases:
    - Property deep dive: Zillow enrichment + skip trace + compliance + AI analysis
    - Market research: Compare properties + trends + neighborhood data
    - Due diligence: Owner research + compliance + contract requirements
    """
    __tablename__ = "research"
    __table_args__ = (
        Index("ix_research_property_id", "property_id"),
        Index("ix_research_status", "status"),
        Index("ix_research_agent_id", "agent_id"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Research configuration
    research_type = Column(Enum(ResearchType), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)

    # Research parameters
    parameters = Column(JSON, nullable=True)  # Custom parameters for research
    endpoints_to_call = Column(JSON, nullable=True)  # List of endpoints to hit

    # Status tracking
    status = Column(Enum(ResearchStatus), default=ResearchStatus.PENDING)
    progress = Column(Integer, default=0)  # Percentage complete (0-100)
    current_step = Column(String, nullable=True)  # Current research step

    # Results
    results = Column(JSON, nullable=True)  # Aggregated research results
    error_message = Column(Text, nullable=True)

    # Metadata
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    property = relationship("Property", backref="research_jobs")
    agent = relationship("Agent", backref="research_jobs")
