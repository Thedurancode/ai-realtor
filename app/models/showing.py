import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ShowingStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ShowingType(str, enum.Enum):
    IN_PERSON = "in_person"
    VIRTUAL = "virtual"
    OPEN_HOUSE = "open_house"


class Showing(Base):
    __tablename__ = "showings"
    __table_args__ = (
        Index("ix_showings_property_id", "property_id"),
        Index("ix_showings_status", "status"),
        Index("ix_showings_scheduled_at", "scheduled_at"),
        Index("ix_showings_agent_id", "agent_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    showing_type = Column(Enum(ShowingType), default=ShowingType.IN_PERSON)
    status = Column(Enum(ShowingStatus), default=ShowingStatus.SCHEDULED)

    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=30)
    notes = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)

    attendee_name = Column(String, nullable=True)
    attendee_phone = Column(String, nullable=True)
    attendee_email = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    property = relationship("Property")
    agent = relationship("Agent")
    client = relationship("Client", back_populates="showings")
