from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TalkingHeadVideo(Base):
    """Branded talking head video generated via HeyGen."""
    __tablename__ = "talking_head_videos"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    script = Column(Text, nullable=False)

    # Status: pending → creating_avatar → generating → assembling → completed / failed
    status = Column(String(50), nullable=False, default="pending")
    error = Column(Text, nullable=True)

    # HeyGen references
    heygen_video_id = Column(String(100), nullable=True)
    heygen_avatar_id = Column(String(100), nullable=True)

    # Result
    video_url = Column(String(500), nullable=True)
    duration = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent = relationship("Agent", backref="talking_head_videos")
