from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    city = Column(String, nullable=True)
    license_number = Column(String, unique=True, nullable=True)
    api_key_hash = Column(String(64), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    properties = relationship("Property", back_populates="agent")
    preferences = relationship("AgentPreference", back_populates="agent")
    installed_skills = relationship("AgentSkill", back_populates="agent")
    workspace = relationship("Workspace", back_populates="agents")
    brand = relationship("AgentBrand", back_populates="agent", uselist=False)
    onboarding = relationship("AgentOnboarding", back_populates="agent", uselist=False)
    render_jobs = relationship("RenderJob", back_populates="agent")
    timeline_projects = relationship("TimelineProject", back_populates="agent")
    contact_lists = relationship("ContactList", back_populates="agent")
    # Temporarily commented to fix circular import
    # phone_numbers = relationship("PhoneNumber", back_populates="agent")
    # phone_calls = relationship("PhoneCall", back_populates="agent")
    # Portal users invited by this agent
    portal_users = relationship("PortalUser", back_populates="agent")
    # Calendar integrations and events
    calendar_connections = relationship("CalendarConnection", back_populates="agent")
    calendar_events = relationship("CalendarEvent", back_populates="agent")
