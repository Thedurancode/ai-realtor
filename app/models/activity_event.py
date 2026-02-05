"""
Activity Event model for tracking MCP tool calls and API requests
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum


class ActivityEventType(enum.Enum):
    """Types of activity events"""
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    VOICE_COMMAND = "voice_command"
    SYSTEM_EVENT = "system_event"


class ActivityEventStatus(enum.Enum):
    """Status of activity events"""
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"


class ActivityEvent(Base):
    """Activity Event model"""
    __tablename__ = "activity_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    tool_name = Column(String(255), nullable=False, index=True)
    user_source = Column(String(255), nullable=True)  # e.g., "Claude Desktop", "Web UI", "Voice Assistant"
    event_type = Column(SQLEnum(ActivityEventType), nullable=False, index=True)
    status = Column(SQLEnum(ActivityEventStatus), default=ActivityEventStatus.PENDING, nullable=False)

    # JSON data field for additional information (renamed from metadata to avoid SQLAlchemy reserved word)
    data = Column(Text, nullable=True)  # JSON string for flexible data storage

    # Duration in milliseconds (nullable until result is received)
    duration_ms = Column(Integer, nullable=True)

    # Error details if applicable
    error_message = Column(Text, nullable=True)
