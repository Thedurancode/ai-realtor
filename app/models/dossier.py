from sqlalchemy import Boolean, Column, Index, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Dossier(Base):
    __tablename__ = "dossiers"
    __table_args__ = (
        Index("ix_dossiers_current", "job_id", "is_current"),
    )

    id = Column(Integer, primary_key=True, index=True)
    research_property_id = Column(Integer, ForeignKey("research_properties.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("agentic_jobs.id"), nullable=False, index=True)

    markdown = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)

    is_current = Column(Boolean, nullable=False, server_default="true")
    superseded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    research_property = relationship("ResearchProperty", back_populates="dossiers")
    job = relationship("AgenticJob", back_populates="dossiers")
