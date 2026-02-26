"""VideoGen AI Video Generation Models"""
from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class VideoGenVideo(Base):
    """AI-generated avatar videos from VideoGen"""
    __tablename__ = "videogen_videos"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)

    # VideoGen API data
    video_id = Column(String(100), unique=True, nullable=False)  # VideoGen video ID
    avatar_id = Column(String(100), nullable=False)  # Avatar used
    voice_id = Column(String(100), nullable=True)  # Voice used
    script = Column(Text, nullable=False)  # Script spoken by avatar
    script_type = Column(String(50), default="promotion")  # promotion, market_update, open_house, custom

    # Video details
    video_url = Column(Text, nullable=True)  # Download URL
    aspect_ratio = Column(String(10), default="16:9")  # 16:9 or 9:16
    duration_seconds = Column(Integer, nullable=True)  # Video length

    # Postiz integration
    postiz_media_id = Column(String(100), nullable=True)  # Postiz media ID
    postiz_media_url = Column(Text, nullable=True)  # Postiz media URL
    postiz_post_id = Column(String(100), nullable=True)  # Postiz post ID

    # Social media posting
    platforms = Column(JSON, nullable=True)  # ["instagram", "tiktok", "youtube"]
    platforms_posted = Column(JSON, nullable=True)  # Track which platforms posted
    post_status = Column(String(50), default="pending")  # pending, posted, failed

    # Status tracking
    status = Column(String(50), default="processing")  # processing, completed, failed, posted
    generation_started_at = Column(DateTime(timezone=True), nullable=True)
    generation_completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    # Extra data (renamed from metadata to avoid SQLAlchemy conflict)
    extra_data = Column(JSON, nullable=True)  # Additional data
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("Agent")
    property = relationship("Property")


class VideoGenAvatar(Base):
    """Available AI avatars from VideoGen"""
    __tablename__ = "videogen_avatars"

    id = Column(Integer, primary_key=True, index=True)
    avatar_id = Column(String(100), unique=True, nullable=False)  # VideoGen avatar ID
    avatar_name = Column(String(255), nullable=False)
    preview_image_url = Column(Text, nullable=True)
    gender = Column(String(20), nullable=True)  # male, female
    age = Column(String(20), nullable=True)  # young, middle, senior
    ethnicity = Column(String(50), nullable=True)
    category = Column(String(50), nullable=True)  # professional, casual, character

    # Voice compatibility
    default_voice_id = Column(String(100), nullable=True)
    supported_languages = Column(JSON, nullable=True)  # ["en-US", "es-ES"]

    # Usage stats
    times_used = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Settings
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)  # Some avatars require higher tier

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class VideoGenScriptTemplate(Base):
    """Reusable video script templates"""
    __tablename__ = "videogen_script_templates"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    template_name = Column(String(255), nullable=False)
    template_category = Column(String(50), nullable=False)  # promotion, market_update, open_house, brand
    template_type = Column(String(50), default="property")  # property, market, brand, custom

    # Template content
    script_template = Column(Text, nullable=False)
    variables = Column(JSON, nullable=True)  # ["{city}", "{price}", "{bedrooms}"]

    # Video settings
    default_avatar_id = Column(String(100), nullable=True)
    default_aspect_ratio = Column(String(10), default="16:9")
    default_duration_target = Column(Integer, default=60)  # Target seconds

    # Usage stats
    times_used = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("Agent")


class VideoGenSettings(Base):
    """Agent VideoGen preferences and settings"""
    __tablename__ = "videogen_settings"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), unique=True, nullable=False)

    # Default avatar settings
    default_avatar_id = Column(String(100), nullable=True)
    default_voice_id = Column(String(100), nullable=True)
    default_aspect_ratio = Column(String(10), default="16:9")
    default_background = Column(String(20), default="#FFFFFF")

    # Auto-posting settings
    auto_post_to_social = Column(Boolean, default=False)
    default_platforms = Column(JSON, nullable=True)  # ["instagram", "tiktok"]

    # Quality settings
    video_quality = Column(String(20), default="1080p")  # 720p, 1080p, 4k

    # Branding
    use_branding = Column(Boolean, default=True)
    intro_text = Column(String(255), nullable=True)
    outro_text = Column(String(255), nullable=True)
    call_to_action = Column(String(255), nullable=True)

    # API settings
    api_key = Column(String(500), nullable=True)  # Encrypted VideoGen API key
    monthly_quota = Column(Integer, nullable=True)  # Videos per month
    videos_used_this_month = Column(Integer, default=0)
    quota_reset_date = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("Agent")
