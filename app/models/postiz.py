"""Postiz Social Media Marketing Integration"""
from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class PostizAccount(Base):
    """Postiz account connection"""
    __tablename__ = "postiz_accounts"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Postiz API Credentials
    api_key = Column(String(500), nullable=False)
    workspace_id = Column(String(100), nullable=True)
    account_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    # Connected Social Accounts
    connected_platforms = Column(JSON, nullable=True)  # {facebook, instagram, twitter, linkedin, tiktok}
    platform_tokens = Column(JSON, nullable=True)  # encrypted tokens for each platform

    # Settings
    default_timezone = Column(String(50), default="America/New_York")
    auto_publish = Column(Boolean, default=False)
    notify_on_publish = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("Agent")
    posts = relationship("PostizPost", back_populates="account", cascade="all, delete-orphan")


class PostizPost(Base):
    """Social media posts scheduled via Postiz"""
    __tablename__ = "postiz_posts"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("postiz_accounts.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)

    # Post Content
    content_type = Column(String(50), nullable=False)  # property_promo, market_update, brand_awareness, testimonial, open_house
    title = Column(String(255), nullable=True)
    caption = Column(Text, nullable=False)
    hashtags = Column(JSON, nullable=True)  # list of hashtags
    mention_accounts = Column(JSON, nullable=True)  # accounts to tag

    # Media Assets
    media_urls = Column(JSON, nullable=True)  # list of image/video URLs
    media_type = Column(String(50), default="image")  # image, video, carousel, story
    thumbnail_url = Column(String(500), nullable=True)

    # Platform-Specific Content
    platform_content = Column(JSON, nullable=True)  # {facebook: {...}, instagram: {...}, twitter: {...}}
    platform_optimizations = Column(JSON, nullable=True)  # platform-specific tweaks

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_timezone = Column(String(50), default="America/New_York")
    publish_immediately = Column(Boolean, default=False)

    # Targeting (for promoted posts)
    target_audience = Column(JSON, nullable=True)  # age, location, interests
    boost_post = Column(Boolean, default=False)
    boost_budget = Column(Float, nullable=True)

    # Post Status
    status = Column(String(50), default="draft")  # draft, scheduled, publishing, published, failed
    post_id_postiz = Column(String(100), nullable=True)  # Postiz post ID
    post_ids_platforms = Column(JSON, nullable=True)  # {facebook: "123", instagram: "456"}

    # Analytics
    analytics = Column(JSON, nullable=True)  # {impressions, reach, engagement, clicks, shares}
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    # AI Generation
    generated_by = Column(String(50), default="ai")  # ai, manual
    generation_model = Column(String(100), nullable=True)
    ai_prompt = Column(Text, nullable=True)  # prompt used for generation

    # Brand Integration
    use_branding = Column(Boolean, default=True)
    brand_applied = Column(JSON, nullable=True)  # which brand elements were used

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("Agent")
    account = relationship("PostizAccount", back_populates="posts")
    property = relationship("Property")


class PostizCalendar(Base):
    """Content calendar for planning posts"""
    __tablename__ = "postiz_calendars"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    calendar_name = Column(String(255), nullable=False)
    calendar_type = Column(String(50), default="marketing")  # marketing, properties, brand, events

    # Schedule Configuration
    posting_frequency = Column(JSON, nullable=True)  # {facebook: "daily", instagram: "3x_weekly"}
    best_times_to_post = Column(JSON, nullable=True)  # {facebook: ["9am", "5pm"], instagram: ["12pm", "7pm"]}
    content_mix = Column(JSON, nullable=True)  # {properties: 60, market_updates: 20, brand: 20}

    # Automated Scheduling
    auto_schedule_properties = Column(Boolean, default=True)
    auto_schedule_market_reports = Column(Boolean, default=True)
    auto_schedule_open_houses = Column(Boolean, default=True)

    # Calendar Settings
    default_timezone = Column(String(50), default="America/New_York")
    queue_capacity = Column(Integer, default=30)  # max posts in queue

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("Agent")


class PostizTemplate(Base):
    """Reusable post templates"""
    __tablename__ = "postiz_templates"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    template_name = Column(String(255), nullable=False)
    template_category = Column(String(100), nullable=False)  # property_promo, open_house, market_report, just_listed, price_reduction
    template_type = Column(String(50), default="property")  # property, brand, market, custom

    # Template Content
    caption_template = Column(Text, nullable=False)  # Use {{property}}, {{price}}, {{address}} placeholders
    hashtag_template = Column(JSON, nullable=True)  # list of hashtag templates
    mention_template = Column(JSON, nullable=True)

    # Media Guidance
    media_type = Column(String(50), default="image")  # image, video, carousel
    media_count = Column(Integer, default=1)  # number of images
    media_guidance = Column(Text, nullable=True)  # instructions for media selection

    # Platform Variations
    platform_variations = Column(JSON, nullable=True)  # {facebook: {...}, instagram: {...}}

    # AI Enhancement
    ai_generate_caption = Column(Boolean, default=True)
    ai_optimize_for_platform = Column(Boolean, default=True)

    # Usage Stats
    times_used = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("Agent")


class PostizAnalytics(Base):
    """Aggregated social media analytics"""
    __tablename__ = "postiz_analytics"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly

    # Platform Metrics
    metrics = Column(JSON, nullable=True)  # {
    #   facebook: {followers, impressions, reach, engagement, engagement_rate, posts_published},
    #   instagram: {followers, impressions, reach, engagement, engagement_rate, posts_published},
    #   twitter: {...},
    #   linkedin: {...}
    # }

    # Top Performing Content
    top_posts = Column(JSON, nullable=True)  # list of best performing posts
    top_hashtags = Column(JSON, nullable=True)  # best performing hashtags
    top_times = Column(JSON, nullable=True)  # best posting times

    # Audience Insights
    audience_demographics = Column(JSON, nullable=True)  # age, gender, location
    audience_growth = Column(JSON, nullable=True)  # growth over period

    # Content Performance
    content_type_performance = Column(JSON, nullable=True)  # {property_promo: {...}, market_update: {...}}
    media_type_performance = Column(JSON, nullable=True)  # {image: {...}, video: {...}, carousel: {...}}

    # Engagement Breakdown
    engagement_by_day = Column(JSON, nullable=True)  # daily engagement stats
    engagement_by_platform = Column(JSON, nullable=True)  # platform comparison

    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("Agent")


class PostizCampaign(Base):
    """Multi-post marketing campaigns"""
    __tablename__ = "postiz_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)

    campaign_name = Column(String(255), nullable=False)
    campaign_type = Column(String(50), nullable=False)  # property_launch, open_house, brand_awareness, market_report
    campaign_status = Column(String(50), default="draft")  # draft, active, paused, completed

    # Campaign Goals
    target_impressions = Column(Integer, nullable=True)
    target_engagement_rate = Column(Float, nullable=True)
    target_clicks = Column(Integer, nullable=True)
    target_leads = Column(Integer, nullable=True)

    # Campaign Posts
    posts = Column(JSON, nullable=True)  # list of post IDs in this campaign
    post_count = Column(Integer, default=0)

    # Schedule
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    # Budget (for boosted posts)
    total_budget = Column(Float, nullable=True)
    spent_budget = Column(Float, default=0.0)

    # Performance Tracking
    metrics = Column(JSON, nullable=True)  # aggregate metrics across all posts
    goal_progress = Column(JSON, nullable=True)  # {impressions: 50%, engagement: 75%}

    # AI Settings
    auto_generate_content = Column(Boolean, default=True)
    auto_optimize_schedule = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("Agent")
    property = relationship("Property")
