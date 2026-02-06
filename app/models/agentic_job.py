import enum

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AgenticJobStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AgenticJob(Base):
    __tablename__ = "agentic_jobs"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String(64), nullable=False, unique=True, index=True)

    research_property_id = Column(Integer, ForeignKey("research_properties.id"), nullable=False, index=True)

    status = Column(Enum(AgenticJobStatus), nullable=False, default=AgenticJobStatus.PENDING)
    progress = Column(Integer, nullable=False, default=0)
    current_step = Column(String(255), nullable=True)

    strategy = Column(String(32), nullable=False, default="wholesale")
    assumptions = Column(JSON, nullable=True)
    limits = Column(JSON, nullable=True)

    results = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    research_property = relationship("ResearchProperty", back_populates="jobs")
    evidence_items = relationship("EvidenceItem", back_populates="job")
    comp_sales = relationship("CompSale", back_populates="job")
    comp_rentals = relationship("CompRental", back_populates="job")
    underwriting_items = relationship("Underwriting", back_populates="job")
    risk_scores = relationship("RiskScore", back_populates="job")
    dossiers = relationship("Dossier", back_populates="job")
    worker_runs = relationship("WorkerRun", back_populates="job")
