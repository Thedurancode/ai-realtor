from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AgentOnboarding(Base):
    """
    Store complete onboarding data from the landing page wizard.
    Contains all personal, business, and preference data collected during signup.
    """
    __tablename__ = "agent_onboarding"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, unique=True)

    # Personal Information
    first_name = Column(String(100))
    last_name = Column(String(100))
    age = Column(Integer, nullable=True)
    city = Column(String(100))
    address = Column(Text, nullable=True)
    phone = Column(String(50))
    email = Column(String(255))
    license_number = Column(String(100), nullable=True)  # Real estate license number

    # Business Information
    business_name = Column(String(255))
    business_card_image = Column(Text, nullable=True)  # URL to uploaded business card image
    logo_url = Column(Text, nullable=True)

    # Brand Colors (JSON object with color scheme)
    colors = Column(JSON, nullable=True)

    # Schedule (JSON object with daily schedules)
    schedule = Column(JSON, nullable=True)
    weekend_schedule = Column(JSON, nullable=True)

    # Contacts and Social Media
    contacts_uploaded = Column(Boolean, default=False)
    social_media = Column(JSON, nullable=True)

    # Preferences
    music_preferences = Column(JSON, nullable=True)  # List of genres
    contracts_used = Column(JSON, nullable=True)  # List of contract types
    calendar_connected = Column(Boolean, default=False)

    # Business Locations
    primary_market = Column(String(255))
    secondary_markets = Column(Text, nullable=True)
    service_radius = Column(String(100), nullable=True)
    office_locations = Column(Text, nullable=True)

    # AI Assistant Configuration
    assistant_name = Column(String(100))
    assistant_style = Column(String(100))
    personality_traits = Column(JSON, nullable=True)  # Trait scores

    # Metadata
    onboarded_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    onboarding_complete = Column(Boolean, default=False)

    # Relationships
    agent = relationship("Agent", back_populates="onboarding")

    def __repr__(self):
        return f"<AgentOnboarding(agent_id={self.agent_id}, name={self.first_name} {self.last_name})>"
