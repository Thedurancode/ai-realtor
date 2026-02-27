"""
Property Website Model

AI-generated landing pages for properties
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, JSON, TIMESTAMP, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class PropertyWebsite(Base):
    """AI-generated websites for property marketing"""
    __tablename__ = "property_websites"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)

    # Website identification
    website_name = Column(String(255), nullable=False)  # e.g., "123 Main St - Luxury Condo"
    website_slug = Column(String(255), unique=True, nullable=False, index=True)  # URL slug

    # Website configuration
    website_type = Column(String(50), nullable=False, default="landing_page")  # landing_page, single_page, full_site
    template = Column(String(100), nullable=False, default="modern")  # modern, luxury, minimal, corporate
    theme = Column(JSON, nullable=True)  # {"primary_color": "#3b82f6", "font": "Inter", "layout": "contemporary"}

    # AI-generated content
    content = Column(JSON, nullable=True)  # Hero, sections, images, forms, etc.

    # Publishing
    custom_domain = Column(String(255), nullable=True)  # Optional custom domain
    is_published = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    published_at = Column(TIMESTAMP, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default="NOW()", nullable=False)
    updated_at = Column(TIMESTAMP, server_default="NOW()", onupdate="NOW()", nullable=False)

    # Relationships
    property = relationship("Property", back_populates="websites")
    agent = relationship("Agent", back_populates="websites")
    analytics = relationship("WebsiteAnalytics", back_populates="website", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PropertyWebsite(id={self.id}, name='{self.website_name}', slug='{self.website_slug}')>"


class WebsiteAnalytics(Base):
    """Website visitor tracking and lead capture"""
    __tablename__ = "website_analytics"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("property_websites.id"), nullable=False, index=True)

    # Event tracking
    event_type = Column(String(50), nullable=False, index=True)  # view, contact_form_submit, inquiry, phone_click
    event_data = Column(JSON, nullable=True)  # Form data, inquiry details, etc.

    # Visitor info
    visitor_ip = Column(String(50), nullable=True)
    user_agent = Column(String, nullable=True)
    referrer = Column(String, nullable=True)

    created_at = Column(TIMESTAMP, server_default="NOW()", nullable=False, index=True)

    # Relationship
    website = relationship("PropertyWebsite", back_populates="analytics")

    def __repr__(self):
        return f"<WebsiteAnalytics(id={self.id}, event='{self.event_type}', website_id={self.website_id})>"
