"""Voice Agent Call model for tracking AI voice agent conversations."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index

from app.database import Base


class VoiceAgentCall(Base):
    """Record of voice agent calls where Claude executes tools by voice."""

    __tablename__ = "voice_agent_calls"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String, unique=True, nullable=False, index=True)
    phone_number = Column(String, nullable=True)
    direction = Column(String, nullable=False, default="inbound")  # 'inbound' or 'outbound'
    status = Column(String, nullable=False, default="started")  # started, in_progress, completed, failed

    # Conversation data
    transcript = Column(Text, nullable=True)  # Full conversation transcript
    actions_taken = Column(Text, nullable=True)  # JSON string of tools called and results

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_voice_agent_call_status", "status"),
        Index("idx_voice_agent_call_created", "created_at"),
    )

    def __repr__(self):
        return f"<VoiceAgentCall(id={self.id}, call_id={self.call_id}, direction={self.direction}, status={self.status})>"
