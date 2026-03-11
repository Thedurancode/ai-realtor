"""Models for Shotstack video enhancements.

New tables:
  - social_clips: Short-form vertical videos for social media
  - video_batch_jobs: Batch rendering across multiple properties
  - video_batch_items: Individual items within a batch
  - template_marketplace: Pre-built templates agents can browse
  - video_thumbnails: Generated preview thumbnails
  - shotstack_webhooks: Webhook delivery log for render callbacks
  - cma_videos: Comparable Market Analysis video jobs
  - listing_slideshows: Simple photo slideshow videos
"""
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey,
    JSON, Boolean, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SocialClip(Base):
    """Short-form vertical video for Instagram Reels, TikTok, YouTube Shorts."""
    __tablename__ = "social_clips"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True, index=True)
    # 15, 30, or 60 seconds
    duration_target = Column(Integer, nullable=False, default=30)
    # 9:16 (vertical), 1:1 (square), 16:9 (landscape)
    aspect_ratio = Column(String(10), nullable=False, default="9:16")
    # resolution: sd (576x1024), hd (720x1280), 1080 (1080x1920)
    resolution = Column(String(10), nullable=False, default="hd")
    # platform target: instagram_reels, tiktok, youtube_shorts, all
    platform = Column(String(50), nullable=False, default="all")
    style = Column(String(50), nullable=False, default="professional")
    script = Column(Text, nullable=True)
    caption_text = Column(Text, nullable=True)
    hashtags = Column(JSON, nullable=True)
    # Music / audio
    background_music_url = Column(String(500), nullable=True)
    voiceover_url = Column(String(500), nullable=True)
    # Render tracking
    status = Column(String(50), nullable=False, default="pending")
    error = Column(Text, nullable=True)
    shotstack_render_id = Column(String(100), nullable=True)
    video_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    timeline_json = Column(JSON, nullable=True)
    actual_duration = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent = relationship("Agent", backref="social_clips")
    property = relationship("Property", backref="social_clips")


class VideoBatchJob(Base):
    """Batch video rendering job spanning multiple properties."""
    __tablename__ = "video_batch_jobs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    name = Column(String(200), nullable=True)
    # Type: property_video, social_clip, slideshow, brand_video
    job_type = Column(String(50), nullable=False, default="property_video")
    style = Column(String(50), nullable=False, default="luxury")
    status = Column(String(50), nullable=False, default="pending")
    total_items = Column(Integer, nullable=False, default=0)
    completed_items = Column(Integer, nullable=False, default=0)
    failed_items = Column(Integer, nullable=False, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent = relationship("Agent", backref="video_batch_jobs")
    items = relationship("VideoBatchItem", back_populates="batch", cascade="all, delete-orphan")


class VideoBatchItem(Base):
    """Individual item within a batch rendering job."""
    __tablename__ = "video_batch_items"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("video_batch_jobs.id"), nullable=False, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, index=True)
    # Links to the individual video job created for this item
    video_job_id = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    video_url = Column(String(500), nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    batch = relationship("VideoBatchJob", back_populates="items")
    property = relationship("Property", backref="video_batch_items")


class TemplateMarketplace(Base):
    """Pre-built video templates agents can browse and render."""
    __tablename__ = "template_marketplace"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    # Category: property_showcase, brand_intro, social_clip, market_report, slideshow
    category = Column(String(50), nullable=False, default="property_showcase")
    # Style tag for filtering
    style = Column(String(50), nullable=False, default="professional")
    # Preview image URL
    preview_image_url = Column(String(500), nullable=True)
    # Preview video URL (short demo)
    preview_video_url = Column(String(500), nullable=True)
    # Shotstack template ID (if saved to Shotstack)
    shotstack_template_id = Column(String(100), nullable=True)
    # The full Edit JSON for this template
    template_json = Column(JSON, nullable=False)
    # Merge fields available: [{"key": "HEADLINE", "label": "Headline", "default": "Dream Home"}]
    merge_fields = Column(JSON, nullable=True)
    # Aspect ratio: 16:9, 9:16, 1:1
    aspect_ratio = Column(String(10), nullable=False, default="16:9")
    # Duration in seconds
    duration = Column(Float, nullable=True)
    # Metadata
    tags = Column(JSON, nullable=True)
    is_featured = Column(Boolean, nullable=False, default=False)
    is_premium = Column(Boolean, nullable=False, default=False)
    use_count = Column(Integer, nullable=False, default=0)
    # Created by agent (null = system template)
    created_by_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    created_by = relationship("Agent", backref="marketplace_templates")


class VideoThumbnail(Base):
    """Generated preview thumbnail for a video."""
    __tablename__ = "video_thumbnails"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    # Source: property_video_job, social_clip, slideshow, cma_video
    source_type = Column(String(50), nullable=False)
    source_id = Column(Integer, nullable=False, index=True)
    # Shotstack render ID for the thumbnail
    shotstack_render_id = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    thumbnail_url = Column(String(500), nullable=True)
    # Frame time in seconds (where to grab the frame)
    frame_time = Column(Float, nullable=False, default=2.0)
    timeline_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    agent = relationship("Agent", backref="video_thumbnails")


class ShotstackWebhook(Base):
    """Log of Shotstack webhook deliveries for render callbacks."""
    __tablename__ = "shotstack_webhooks"

    id = Column(Integer, primary_key=True, index=True)
    render_id = Column(String(100), nullable=False, index=True)
    # Which job this render belongs to
    job_type = Column(String(50), nullable=True)  # property_video, social_clip, etc.
    job_id = Column(Integer, nullable=True, index=True)
    status = Column(String(50), nullable=False)
    video_url = Column(String(500), nullable=True)
    # Raw webhook payload
    payload = Column(JSON, nullable=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now())


class CmaVideo(Base):
    """Comparable Market Analysis video job."""
    __tablename__ = "cma_videos"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, index=True)
    style = Column(String(50), nullable=False, default="professional")
    # Number of comps to include
    max_comps = Column(Integer, nullable=False, default=5)
    # Include rental comps?
    include_rentals = Column(Boolean, nullable=False, default=False)
    # Generated content
    script = Column(Text, nullable=True)
    comp_data = Column(JSON, nullable=True)  # Snapshot of comps used
    # Render tracking
    status = Column(String(50), nullable=False, default="pending")
    error = Column(Text, nullable=True)
    shotstack_render_id = Column(String(100), nullable=True)
    video_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    duration = Column(Float, nullable=True)
    timeline_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent = relationship("Agent", backref="cma_videos")
    property = relationship("Property", backref="cma_videos")


class ListingSlideshow(Base):
    """Simple photo slideshow video — no HeyGen/TTS needed."""
    __tablename__ = "listing_slideshows"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, index=True)
    style = Column(String(50), nullable=False, default="luxury")
    # Photo URLs to use (from Zillow, uploads, etc.)
    photo_urls = Column(JSON, nullable=False)
    # Text overlays
    title_text = Column(String(300), nullable=True)
    subtitle_text = Column(String(300), nullable=True)
    cta_text = Column(String(300), nullable=True)
    # Music
    background_music_url = Column(String(500), nullable=True)
    # Aspect ratio: 16:9, 9:16, 1:1
    aspect_ratio = Column(String(10), nullable=False, default="16:9")
    # Seconds per photo
    seconds_per_photo = Column(Float, nullable=False, default=4.0)
    # Render tracking
    status = Column(String(50), nullable=False, default="pending")
    error = Column(Text, nullable=True)
    shotstack_render_id = Column(String(100), nullable=True)
    video_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    duration = Column(Float, nullable=True)
    timeline_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent = relationship("Agent", backref="listing_slideshows")
    property = relationship("Property", backref="listing_slideshows")
