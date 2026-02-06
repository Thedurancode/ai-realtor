from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ActivityEventCreate(BaseModel):
    """Create activity event request"""
    tool_name: str
    user_source: Optional[str] = "Unknown"
    event_type: str = "tool_call"
    status: str = "pending"
    metadata: Optional[dict] = None


class ActivityEventUpdate(BaseModel):
    """Update activity event request"""
    status: Optional[str] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None


class ActivityEventResponse(BaseModel):
    """Activity event response"""
    id: int
    timestamp: datetime
    tool_name: str
    user_source: Optional[str]
    event_type: str
    status: str
    metadata: Optional[str]
    duration_ms: Optional[int]
    error_message: Optional[str]

    class Config:
        from_attributes = True
