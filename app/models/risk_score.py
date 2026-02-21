from sqlalchemy import Boolean, Column, Index, Integer, DateTime, Text, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"
    __table_args__ = (
        Index("ix_risk_scores_current", "job_id", "is_current"),
    )

    id = Column(Integer, primary_key=True, index=True)
    research_property_id = Column(Integer, ForeignKey("research_properties.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("agentic_jobs.id"), nullable=False, index=True)

    title_risk = Column(Float, nullable=True)
    data_confidence = Column(Float, nullable=True)
    compliance_flags = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    is_current = Column(Boolean, nullable=False, server_default="true")
    superseded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    research_property = relationship("ResearchProperty", back_populates="risk_scores")
    job = relationship("AgenticJob", back_populates="risk_scores")
