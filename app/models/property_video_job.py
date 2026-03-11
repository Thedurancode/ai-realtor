from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PropertyVideoJob(Base):
    __tablename__ = "property_video_jobs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True, index=True)
    script = Column(Text, nullable=True)
    style = Column(String(50), nullable=False, server_default="luxury")
    status = Column(String(50), nullable=False, server_default="pending")
    pipeline_type = Column(String(50), nullable=True, server_default="legacy")
    error = Column(Text, nullable=True)
    shotstack_render_id = Column(String(100), nullable=True)
    video_url = Column(String(500), nullable=True)
    duration = Column(Float, nullable=True)
    stock_videos_used = Column(JSON, nullable=True)
    timeline_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent = relationship("Agent", backref="property_video_jobs")
    property = relationship("Property", backref="property_video_jobs")
