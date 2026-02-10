from sqlalchemy import Column, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.database import Base


class Dossier(Base):
    __tablename__ = "dossiers"

    id = Column(Integer, primary_key=True, index=True)
    research_property_id = Column(Integer, ForeignKey("research_properties.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("agentic_jobs.id"), nullable=False, index=True)

    markdown = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)

    embedding = Column(Vector(1536), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    research_property = relationship("ResearchProperty", back_populates="dossiers")
    job = relationship("AgenticJob", back_populates="dossiers")
