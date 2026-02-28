"""Property Video Model

Enhanced property video generation with avatar + property footage + assembly.
Orchestrates HeyGen avatars, PixVerse footage, and FFmpeg assembly.
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class VideoTypeEnum(str, enum.Enum):
    """Types of property videos"""
    PROPERTY_TOUR = "property_tour"
    AGENT_INTRO = "agent_intro"
    MARKET_UPDATE = "market_update"
    JUST_SOLD = "just_sold"
    NEW_LISTING = "new_listing"


class VideoGenerationStatus(str, enum.Enum):
    """Status of video generation process"""
    DRAFT = "draft"
    GENERATING_SCRIPT = "generating_script"
    SCRIPT_COMPLETED = "script_completed"
    GENERATING_VOICEOVER = "generating_voiceover"
    VOICEOVER_COMPLETED = "voiceover_completed"
    GENERATING_INTRO = "generating_intro"
    INTRO_COMPLETED = "intro_completed"
    GENERATING_FOOTAGE = "generating_footage"
    FOOTAGE_COMPLETED = "footage_completed"
    ASSEMBLING_VIDEO = "assembling_video"
    COMPLETED = "completed"
    FAILED = "failed"


class PropertyVideo(Base):
    """
    Enhanced property video with agent avatar and AI-generated footage.

    Orchestrates multi-step generation:
    1. Script generation (Claude AI)
    2. Voiceover (ElevenLabs)
    3. Avatar intro/outro (HeyGen)
    4. Property footage (PixVerse/Replicate)
    5. FFmpeg assembly
    6. S3 upload
    """
    __tablename__ = "property_videos"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    agent_profile_id = Column(Integer, ForeignKey("agent_video_profiles.id"), nullable=True)

    # Video configuration
    video_type = Column(String(50), nullable=False)  # VideoTypeEnum
    style = Column(String(50), default="luxury")  # luxury, friendly, professional
    duration_target = Column(Integer, default=60)  # Target duration in seconds

    # Generated content
    generated_script = Column(Text, nullable=False)  # JSON script with sections
    voiceover_url = Column(String(500))  # ElevenLabs audio file URL

    # Avatar videos (HeyGen)
    intro_video_url = Column(String(500))  # Agent intro video
    outro_video_url = Column(String(500))  # Call-to-action video

    # Property footage (PixVerse/Replicate)
    property_clips = Column(JSON)  # Array of video URLs from property photos
    photos_used = Column(JSON)  # Array of photo URLs used for footage

    # Final video
    final_video_url = Column(String(500))  # S3 URL
    thumbnail_url = Column(String(500))  # Thumbnail image URL

    # Metadata
    duration = Column(Float)  # Actual duration in seconds
    resolution = Column(String(20), default="1080p")
    file_size = Column(Float)  # Size in bytes

    # Generation tracking
    status = Column(String(50), default=VideoGenerationStatus.DRAFT, nullable=False)
    generation_steps = Column(JSON)  # [{"step": "generating_script", "timestamp": "...", "status": "completed"}]
    error_message = Column(Text)

    # Cost tracking
    generation_cost = Column(Float)  # Total cost in USD
    cost_breakdown = Column(JSON)  # {"heygen": 2.00, "pixverse": 0.05, "elevenlabs": 0.03, "assembly": 0.00}

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    agent = relationship("Agent")
    property = relationship("Property")
    agent_profile = relationship("AgentVideoProfile", back_populates="property_videos")
