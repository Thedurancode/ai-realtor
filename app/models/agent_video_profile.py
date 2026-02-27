"""Agent Video Profile Model

Enhanced agent avatar configuration for video generation.
Extends basic VideoGen with custom avatar creation and detailed settings.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AgentVideoProfile(Base):
    """
    Agent video profile for enhanced avatar video generation.

    Stores agent's custom avatar (created from their photo),
    voice preferences, and default scripts for video generation.
    """
    __tablename__ = "agent_video_profiles"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, unique=True)

    # Avatar configuration
    headshot_url = Column(String(500), nullable=False)  # Agent's photo for custom avatar
    heygen_avatar_id = Column(String(100), unique=True, nullable=True)  # HeyGen custom avatar ID

    # Voice configuration (ElevenLabs)
    voice_id = Column(String(100), nullable=False)  # ElevenLabs voice ID
    voice_style = Column(String(50), default="professional")  # professional, friendly, luxury

    # Branding
    background_color = Column(String(7), default="#f8fafc")  # Hex color for avatar background
    use_agent_branding = Column(Boolean, default=True)  # Use AgentBrand colors/logos

    # Default scripts
    default_intro_script = Column(Text)  # Default agent intro script
    default_outro_script = Column(Text)  # Default call-to-action script

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    agent = relationship("Agent", back_populates="video_profile")
    property_videos = relationship("PropertyVideo", back_populates="agent_profile")


# Update Agent model to include relationship
from app.models.agent import Agent
Agent.video_profile = relationship(
    "AgentVideoProfile",
    back_populates="agent",
    uselist=False,
    cascade="all, delete-orphan"
)
