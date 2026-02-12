"""Conversation history model for tracking MCP tool calls."""
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.types import JSON
from sqlalchemy.sql import func

from app.database import Base


class ConversationHistory(Base):
    """Tracks conversation history for voice/MCP sessions."""

    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(128), nullable=False, index=True)
    tool_name = Column(String(128), nullable=False, index=True)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    success = Column(Integer, default=1)  # 1=success, 0=failed
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("ix_conversation_history_session_created", "session_id", "created_at"),
    )
