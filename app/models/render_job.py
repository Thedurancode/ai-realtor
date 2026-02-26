"""Render job model for Remotion video rendering."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.database import Base


class RenderJob(Base):
    """Remotion render job tracking."""
    __tablename__ = "render_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Template configuration
    template_id = Column(String, nullable=False, index=True)
    composition_id = Column(String, nullable=False)

    # Input data
    input_props = Column(JSON, nullable=False)

    # Job state
    status = Column(String, nullable=False, default="queued", index=True)  # queued, rendering, uploading, completed, failed, canceled
    progress = Column(Float, default=0.0)  # 0.0 to 1.0

    # Output
    output_url = Column(Text, nullable=True)
    output_bucket = Column(String, nullable=True)
    output_key = Column(String, nullable=True)

    # Webhook
    webhook_url = Column(Text, nullable=True)
    webhook_sent = Column(String, nullable=True)  # pending, sent, failed

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Progress tracking (from Remotion)
    current_frame = Column(Integer, nullable=True)
    total_frames = Column(Integer, nullable=True)
    eta_seconds = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="render_jobs")

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "template_id": self.template_id,
            "composition_id": self.composition_id,
            "input_props": self.input_props,
            "status": self.status,
            "progress": self.progress,
            "output_url": self.output_url,
            "webhook_url": self.webhook_url,
            "webhook_sent": self.webhook_sent,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "current_frame": self.current_frame,
            "total_frames": self.total_frames,
            "eta_seconds": self.eta_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
