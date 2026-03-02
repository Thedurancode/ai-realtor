"""PVC Voice Database Model
Stores Professional Voice Clones (PVCs) from ElevenLabs.
"""

from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

from app.database import Base


class PVCVoiceStatus:
    """Status of a PVC voice"""
    CREATING = "creating"
    PROCESSING = "processing"
    SEPARATING = "separating"
    TRAINING = "training"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class PVCVoice(Base):
    """
    Professional Voice Clone (PVC) representation.
    """
    __tablename__ = "pvc_voices"

    id = Column(String, primary_key=True, index=True)  # ElevenLabs voice ID

    # Voice metadata
    name = Column(String(100), nullable=False)
    language = Column(String(10), default="en")
    description = Column(Text, nullable=True)

    # Status tracking
    status = Column(String(20), default=PVCVoiceStatus.CREATING, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Speaker separation
    sample_count = Column(Integer, default=0)  # Number of samples uploaded
    speakers_count = Column(Integer, default=0)  # Number of speakers after separation

    # Training info
    model_id = Column(String(100), nullable=True)  # Model ID (e.g., "eleven_multilingual_v2")
    training_progress = Column(String(100), nullable=True)  # Progress JSON
    is_trained = Column(Boolean, default=False, index=True)  # Whether training is complete
    trained_at = Column(DateTime(timezone=True), nullable=True)  # When training completed

    # Relationships
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)  # Optional: Link to agent
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)  # Optional: Link to property

    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional fields as JSON

    def __repr__(self):
        return f"<PVCVoice(id={self.id}, name={self.name}, status={self.status})>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "language": self.language,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "sample_count": self.sample_count,
            "speakers_count": self.speakers_count,
            "model_id": self.model_id,
            "training_progress": self.training_progress,
            "is_trained": self.is_trained,
            "trained_at": self.trained_at.isoformat() if self.trained_at else None,
            "metadata": self.metadata,
        }
