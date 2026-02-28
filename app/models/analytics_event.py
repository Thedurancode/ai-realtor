"""
Analytics Event Tracking Model

Tracks user interactions, conversions, and custom events
for analytics and reporting.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Index
from sqlalchemy.orm import relationship

from app.database import Base


class AnalyticsEvent(Base):
    """
    Track user events for analytics.

    Events include:
    - page_view: User viewed a page
    - property_view: User viewed a property
    - lead_created: New lead captured
    - conversion: Lead converted (scheduled showing, made offer)
    - email_sent: Email campaign sent
    - email_opened: Recipient opened email
    - email_clicked: Recipient clicked link
    - search: User performed a search
    - filter_applied: User applied filters
    - map_view: User viewed map
    - contact_form: User submitted contact form
    - custom: Any custom event
    """

    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_name = Column(String(255), nullable=False)

    # Event properties (flexible JSON schema)
    properties = Column(JSON, nullable=True)

    # Context information
    session_id = Column(String(255), nullable=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(Text, nullable=True)

    # Referrer information
    referrer = Column(String(500), nullable=True)
    utm_source = Column(String(255), nullable=True)
    utm_medium = Column(String(255), nullable=True)
    utm_campaign = Column(String(255), nullable=True)
    utm_term = Column(String(255), nullable=True)
    utm_content = Column(String(255), nullable=True)

    # Property-specific tracking
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True, index=True)

    # Value tracking (for conversions, revenue attribution)
    value = Column(Integer, nullable=True)  # Monetary value in cents
    currency = Column(String(3), default="USD")

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    agent = relationship("Agent", back_populates="analytics_events")
    property = relationship("Property", back_populates="analytics_events")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_analytics_agent_created", "agent_id", "created_at"),
        Index("idx_analytics_type_created", "event_type", "created_at"),
        Index("idx_analytics_property_created", "property_id", "created_at"),
        Index("idx_analytics_session", "session_id", "created_at"),
    )

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "event_type": self.event_type,
            "event_name": self.event_name,
            "properties": self.properties,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "referrer": self.referrer,
            "utm_source": self.utm_source,
            "utm_medium": self.utm_medium,
            "utm_campaign": self.utm_campaign,
            "property_id": self.property_id,
            "value": self.value,
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
