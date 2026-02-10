"""
Property Recap Model

Stores AI-generated summaries of property state that update automatically
when property data changes. Used for phone calls and voice interactions.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.database import Base


class PropertyRecap(Base):
    """AI-generated property recap that updates automatically"""
    __tablename__ = "property_recaps"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, unique=True, index=True)

    # AI-generated content
    recap_text = Column(Text, nullable=False)  # Human-readable summary
    recap_context = Column(JSON, nullable=False)  # Structured data for VAPI/AI

    # Voice-optimized summary (for phone calls)
    voice_summary = Column(Text, nullable=True)  # Short version for TTS

    # Metadata
    version = Column(Integer, default=1)  # Increments on each update
    last_trigger = Column(String(100), nullable=True)  # What caused the update

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Vector embedding for semantic search
    embedding = Column(Vector(1536), nullable=True)

    # Relationships
    property = relationship("Property", back_populates="recap")
