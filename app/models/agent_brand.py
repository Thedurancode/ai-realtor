from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AgentBrand(Base):
    """Agent branding and profile information"""
    __tablename__ = "agent_brands"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, unique=True)

    # Basic Brand Info
    company_name = Column(String(255), nullable=True)
    tagline = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    website_url = Column(String(500), nullable=True)

    # About Section
    bio = Column(Text, nullable=True)
    about_us = Column(Text, nullable=True)
    specialties = Column(JSON, nullable=True)  # List of specialties
    service_areas = Column(JSON, nullable=True)  # List of cities/states
    languages = Column(JSON, nullable=True)  # List of languages spoken

    # Visual Branding
    primary_color = Column(String(7), nullable=True)  # Hex color
    secondary_color = Column(String(7), nullable=True)  # Hex color
    accent_color = Column(String(7), nullable=True)  # Hex color
    background_color = Column(String(7), nullable=True)  # Hex color
    text_color = Column(String(7), nullable=True)  # Hex color

    # Social Media
    social_media = Column(JSON, nullable=True)  # {facebook, twitter, linkedin, instagram, youtube}

    # Contact Display
    display_phone = Column(String(50), nullable=True)
    display_email = Column(String(255), nullable=True)
    office_address = Column(String(500), nullable=True)
    office_phone = Column(String(50), nullable=True)

    # License Info
    license_display_name = Column(String(255), nullable=True)
    license_number = Column(String(100), nullable=True)
    license_states = Column(JSON, nullable=True)  # List of states licensed in

    # Brand Settings
    show_profile = Column(Boolean, default=True)  # Public profile visibility
    show_contact_info = Column(Boolean, default=True)  # Show phone/email on public profile
    show_social_media = Column(Boolean, default=True)  # Show social links

    # Branding Assets
    headshot_url = Column(String(500), nullable=True)
    banner_url = Column(String(500), nullable=True)
    company_badge_url = Column(String(500), nullable=True)

    # Design Templates
    email_template_style = Column(String(50), default="modern")  # modern, classic, minimal
    report_logo_placement = Column(String(20), default="top-left")  # top-left, top-center, top-right

    # SEO & Marketing
    meta_title = Column(String(255), nullable=True)  # SEO title
    meta_description = Column(Text, nullable=True)  # SEO description
    keywords = Column(JSON, nullable=True)  # SEO keywords

    # Tracking
    google_analytics_id = Column(String(50), nullable=True)
    facebook_pixel_id = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    agent = relationship("Agent", back_populates="brand")


# Update Agent model to include brand relationship
from app.models.agent import Agent
Agent.brand = relationship("AgentBrand", back_populates="agent", uselist=False)
