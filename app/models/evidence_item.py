from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class EvidenceItem(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    research_property_id = Column(Integer, ForeignKey("research_properties.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("agentic_jobs.id"), nullable=False, index=True)

    category = Column(String(64), nullable=False)
    claim = Column(Text, nullable=False)
    source_url = Column(String(1000), nullable=False)
    captured_at = Column(DateTime(timezone=True), nullable=False)
    raw_excerpt = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    hash = Column(String(64), nullable=False, unique=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    research_property = relationship("ResearchProperty", back_populates="evidence_items")
    job = relationship("AgenticJob", back_populates="evidence_items")
