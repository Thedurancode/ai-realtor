import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MessageChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PHONE_CALL = "phone_call"
    IN_PERSON = "in_person"
    NOTE = "note"


class MessageDirection(str, enum.Enum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_client_id", "client_id"),
        Index("ix_messages_property_id", "property_id"),
        Index("ix_messages_channel", "channel"),
        Index("ix_messages_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)

    channel = Column(Enum(MessageChannel), nullable=False)
    direction = Column(Enum(MessageDirection), default=MessageDirection.OUTBOUND)
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=False)
    recipient = Column(String, nullable=True)  # email or phone

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    agent = relationship("Agent")
    client = relationship("Client", back_populates="messages")
    property = relationship("Property")
