"""Timeline project model for saved video projects."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.database import Base


class TimelineProject(Base):
    """Saved timeline video project."""
    __tablename__ = "timeline_projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Project metadata
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # Timeline data
    timeline_data = Column(JSON, nullable=False)

    # Render settings
    fps = Column(Integer, default=30)
    width = Column(Integer, default=1080)
    height = Column(Integer, default=1920)

    # Status
    status = Column(String, default="draft")  # draft, rendering, completed

    # Associated render job (if rendered)
    render_job_id = Column(String, ForeignKey("render_jobs.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    rendered_at = Column(DateTime, nullable=True)

    # Relationships
    agent = relationship("Agent", back_populates="timeline_projects")
    render_job = relationship("RenderJob", foreign_keys=[render_job_id])

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "timeline_data": self.timeline_data,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "status": self.status,
            "render_job_id": self.render_job_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "rendered_at": self.rendered_at.isoformat() if self.rendered_at else None,
        }
