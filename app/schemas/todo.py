from pydantic import BaseModel
from datetime import datetime, date

from app.models.todo import TodoStatus, TodoPriority


class TodoBase(BaseModel):
    title: str
    description: str | None = None
    status: TodoStatus = TodoStatus.PENDING
    priority: TodoPriority = TodoPriority.MEDIUM
    due_date: date | None = None


class TodoCreate(TodoBase):
    property_id: int
    contact_id: int | None = None


class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TodoStatus | None = None
    priority: TodoPriority | None = None
    due_date: date | None = None
    contact_id: int | None = None


class TodoResponse(TodoBase):
    id: int
    property_id: int
    contact_id: int | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TodoCreateFromVoice(BaseModel):
    """
    Voice-optimized todo creation.
    Example: "add a todo for 141 throop: schedule inspection"
    Example: "add high priority todo for throop: fix roof leak"
    Example: "add a todo for throop: call the lawyer John about contract"
    """

    address_query: str  # Partial address to find property
    title: str  # The todo title/description
    priority: str | None = None  # "low", "medium", "high", "urgent"
    due_date: str | None = None  # Natural language like "tomorrow", "next week"
    contact_id: int | None = None  # Optional contact ID to associate with todo


class TodoUpdateFromVoice(BaseModel):
    """
    Voice-optimized todo update.
    Example: "mark todo 3 as completed"
    Example: "update todo 2 status to in progress"
    """

    todo_id: int
    status: str | None = None  # "pending", "in_progress", "completed", "cancelled"
    priority: str | None = None


class TodoVoiceResponse(BaseModel):
    """Voice-optimized response after creating/updating todo"""

    todo: TodoResponse
    voice_confirmation: str


class TodoListVoiceResponse(BaseModel):
    """Voice-optimized response for listing todos"""

    todos: list[TodoResponse]
    voice_summary: str
