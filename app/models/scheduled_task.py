"""Scheduled task model for voice-created reminders and recurring automation."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.types import JSON
from sqlalchemy.sql import func
import enum

from app.database import Base


class TaskType(str, enum.Enum):
    REMINDER = "reminder"
    RECURRING = "recurring"
    FOLLOW_UP = "follow_up"
    CONTRACT_CHECK = "contract_check"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    RETRYING = "retrying"


class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(Enum(TaskType, values_callable=lambda x: [e.value for e in x]), nullable=False, default=TaskType.REMINDER)
    status = Column(Enum(TaskStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=TaskStatus.PENDING, index=True)
    enabled = Column(Boolean, nullable=False, default=True, server_default="1")
    name = Column(String(255), nullable=True, index=True)  # Optional unique identifier for scheduled tasks
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    repeat_interval_hours = Column(Integer, nullable=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)

    # Context
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True, index=True)
    action = Column(String(100), nullable=True)
    action_params = Column(JSON, nullable=True)

    # Tracking
    created_by = Column(String(50), default="voice")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
