"""Property notes model for freeform notes attached to properties."""
from sqlalchemy import Column, Index, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class NoteSource(str, enum.Enum):
    VOICE = "voice"
    MANUAL = "manual"
    AI = "ai"
    PHONE_CALL = "phone_call"
    SYSTEM = "system"


class PropertyNote(Base):
    __tablename__ = "property_notes"
    __table_args__ = (
        Index("ix_property_notes_property_id", "property_id"),
        Index("ix_property_notes_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(Enum(NoteSource), default=NoteSource.MANUAL)
    created_by = Column(String, nullable=True)  # agent name, "voice assistant", etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    property = relationship("Property", back_populates="notes")
