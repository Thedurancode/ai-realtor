from sqlalchemy import Column, Index, Integer, String, DateTime, ForeignKey, Enum, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class TodoStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TodoPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Todo(Base):
    __tablename__ = "todos"
    __table_args__ = (
        Index("ix_todos_property_id", "property_id"),
        Index("ix_todos_status", "status"),
        Index("ix_todos_property_status", "property_id", "status"),
        Index("ix_todos_due_date", "due_date"),
        Index("ix_todos_priority_created", "priority", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)

    # Todo details
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(TodoStatus), default=TodoStatus.PENDING)
    priority = Column(Enum(TodoPriority), default=TodoPriority.MEDIUM)

    # Dates
    due_date = Column(Date, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    property = relationship("Property", back_populates="todos")
    contact = relationship("Contact", back_populates="todos")
